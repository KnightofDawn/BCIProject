/* Copyright (c) 2012 Nordic Semiconductor. All Rights Reserved.
 *
 * The information contained herein is property of Nordic Semiconductor ASA.
 * Terms and conditions of usage are described in detail in NORDIC
 * SEMICONDUCTOR STANDARD SOFTWARE LICENSE AGREEMENT.
 *
 * Licensees are granted free, non-transferable use of the information. NO
 * WARRANTY of ANY KIND is provided. This heading must NOT be removed from
 * the file.
 *
 */

/** @file
 *
 * @{
 * @ingroup ble_app_gzll_bluetooth_part
 */

#include "ble_app_gzll_hr.h"
#include <stdint.h>
#include "nordic_common.h"
#include "nrf.h"
#include "app_error.h"
#include "nrf_gpio.h"
#include "ble.h"
#include "ble_srv_common.h"
#include "ble_advdata.h"
#include "ble_bas.h"
#include "ble_hrs.h"
#include "ble_dis.h"
#include "ble_conn_params.h"
#include "ble_sensorsim.h"
#include "ble_stack_handler.h"
#include "app_timer.h"
#include "ble_nrf6310_pins.h"
#include "ble_app_gzll_ui.h"
#include "app_button.h"
#include "ble_app_gzll_common.h"


#define DEVICE_NAME                       "Nordic_BLE_GZL"                           /**< Name of device. Will be included in the advertising data. */
#define MANUFACTURER_NAME                 "NordicSemiconductor"                      /**< Manufacturer. Will be passed to Device Information Service. */
#define APP_ADV_INTERVAL                  40                                         /**< The advertising interval (in units of 0.625 ms. This value corresponds to 25 ms). */
#define APP_ADV_TIMEOUT_IN_SECONDS        180                                        /**< The advertising timeout in units of seconds. */

#define BATTERY_LEVEL_MEAS_INTERVAL       APP_TIMER_TICKS(2000, APP_TIMER_PRESCALER) /**< Battery level measurement interval (ticks). */
#define MIN_BATTERY_LEVEL                 81                                         /**< Minimum battery level as returned by the simulated measurement function. */
#define MAX_BATTERY_LEVEL                 100                                        /**< Maximum battery level as returned by the simulated measurement function. */
#define BATTERY_LEVEL_INCREMENT           1                                          /**< Value by which the battery level is incremented/decremented for each call to the simulated measurement function. */

#define HEART_RATE_MEAS_INTERVAL          APP_TIMER_TICKS(1000, APP_TIMER_PRESCALER) /**< Heart rate measurement interval (ticks). */
#define MIN_HEART_RATE                    140                                        /**< Minimum heart rate as returned by the simulated measurement function. */
#define MAX_HEART_RATE                    160                                        /**< Maximum heart rate as returned by the simulated measurement function. */
#define HEART_RATE_INCREMENT              1                                          /**< Value by which the heart rate is incremented/decremented for each call to the simulated measurement function. */

#define RR_INTERVAL_INTERVAL              APP_TIMER_TICKS(300, APP_TIMER_PRESCALER)  /**< RR interval interval (ticks). */
#define MIN_RR_INTERVAL                   100                                        /**< Minimum RR interval as returned by the simulated measurement function. */
#define MAX_RR_INTERVAL                   500                                        /**< Maximum RR interval as returned by the simulated measurement function. */
#define RR_INTERVAL_INCREMENT             1                                          /**< Value by which the RR interval is incremented/decremented for each call to the simulated measurement function. */

#define SENSOR_CONTACT_DETECTED_INTERVAL  APP_TIMER_TICKS(5000, APP_TIMER_PRESCALER) /**< Sensor Contact Detected toggle interval (ticks). */

#define SECOND_1_25_MS_UNITS              800                                        /**< Definition of 1 second, when 1 unit is 1.25 ms. */
#define SECOND_10_MS_UNITS                100                                        /**< Definition of 1 second, when 1 unit is 10 ms. */
#define MIN_CONN_INTERVAL                 (SECOND_1_25_MS_UNITS / 2)                 /**< Minimum acceptable connection interval (0.5 seconds), Connection interval uses 1.25 ms units. */
#define MAX_CONN_INTERVAL                 (SECOND_1_25_MS_UNITS)                     /**< Maximum acceptable connection interval (1 second), Connection interval uses 1.25 ms units. */
#define SLAVE_LATENCY                     0                                          /**< Slave latency. */
#define CONN_SUP_TIMEOUT                  (4 * SECOND_10_MS_UNITS)                   /**< Connection supervisory timeout (4 seconds), Supervision Timeout uses 10 ms units. */

#define FIRST_CONN_PARAMS_UPDATE_DELAY    APP_TIMER_TICKS(5000, APP_TIMER_PRESCALER) /**< Time from initiating event (connect or start of notification) to first time sd_ble_gap_conn_param_update is called (5 seconds). */
#define NEXT_CONN_PARAMS_UPDATE_DELAY     APP_TIMER_TICKS(5000, APP_TIMER_PRESCALER) /**< Time between each call to sd_ble_gap_conn_param_update after the first (30 seconds). */
#define MAX_CONN_PARAMS_UPDATE_COUNT      3                                          /**< Number of attempts before giving up the connection parameter negotiation. */

#define SEC_PARAM_TIMEOUT                 30                                         /**< Timeout for Pairing Request or Security Request (in seconds). */
#define SEC_PARAM_BOND                    1                                          /**< Perform bonding. */
#define SEC_PARAM_MITM                    0                                          /**< Man In The Middle protection not required. */
#define SEC_PARAM_IO_CAPABILITIES         BLE_GAP_IO_CAPS_NONE                       /**< No I/O capabilities. */
#define SEC_PARAM_OOB                     0                                          /**< Out Of Band data not available. */
#define SEC_PARAM_MIN_KEY_SIZE            7                                          /**< Minimum encryption key size. */
#define SEC_PARAM_MAX_KEY_SIZE            16                                         /**< Maximum encryption key size. */

static ble_gap_sec_params_t   m_sec_params;                                          /**< Security requirements for this application. */
static ble_gap_adv_params_t   m_adv_params;                                          /**< Parameters to be passed to the stack when starting advertising. */
static ble_bas_t              m_bas;                                                 /**< Structure used to identify the battery service. */
static ble_hrs_t              m_hrs;                                                 /**< Structure used to identify the heart rate service. */
static bool                   m_rr_interval_enabled = true;                          /**< Flag for enabling and disabling the registration of new RR interval measurements (the purpose of disabling this is just to test sending HRM without RR interval data. */

static ble_sensorsim_cfg_t    m_battery_sim_cfg;                                     /**< Battery Level sensor simulator configuration. */
static ble_sensorsim_state_t  m_battery_sim_state;                                   /**< Battery Level sensor simulator state. */
static ble_sensorsim_cfg_t    m_heart_rate_sim_cfg;                                  /**< Heart Rate sensor simulator configuration. */
static ble_sensorsim_state_t  m_heart_rate_sim_state;                                /**< Heart Rate sensor simulator state. */
static ble_sensorsim_cfg_t    m_rr_interval_sim_cfg;                                 /**< RR Interval sensor simulator configuration. */
static ble_sensorsim_state_t  m_rr_interval_sim_state;                               /**< RR Interval sensor simulator state. */

static app_timer_id_t         m_battery_timer_id;                                    /**< Battery timer. */
static app_timer_id_t         m_heart_rate_timer_id;                                 /**< Heart rate measurement timer. */
static app_timer_id_t         m_rr_interval_timer_id;                                /**< RR interval timer. */
static app_timer_id_t         m_sensor_contact_timer_id;                             /**< Sensor contact detected timer. */


/**@brief Perform battery measurement, and update Battery Level characteristic in Battery Service.
 */
static void battery_level_update(void)
{
    uint32_t err_code;
    uint8_t  battery_level;
    
    battery_level = (uint8_t)ble_sensorsim_measure(&m_battery_sim_state, &m_battery_sim_cfg);
    
    err_code = ble_bas_battery_level_update(&m_bas, battery_level);
    if (
        (err_code != NRF_SUCCESS)
        &&
        (err_code != NRF_ERROR_INVALID_STATE)
        &&
        (err_code != BLE_ERROR_NO_TX_BUFFERS)
        &&
        (err_code != BLE_ERROR_GATTS_SYS_ATTR_MISSING)
    )
    {
        APP_ERROR_HANDLER(err_code);
    }
}


/**@brief Battery measurement timer timeout handler.
 *
 * @details This function will be called each time the battery level measurement timer expires.
 *
 * @param[in]   p_context   Pointer used for passing some arbitrary information (context) from the
 *                          app_start_timer() call to the timeout handler.
 */
static void battery_level_meas_timeout_handler(void * p_context)
{
    UNUSED_PARAMETER(p_context);
    battery_level_update();
}


/**@brief Heart rate measurement timer timeout handler.
 *
 * @details This function will be called each time the heart rate measurement timer expires.
 *          It will exclude RR Interval data from every third measurement.
 *
 * @param[in]   p_context   Pointer used for passing some arbitrary information (context) from the
 *                          app_start_timer() call to the timeout handler.
 */
static void heart_rate_meas_timeout_handler(void * p_context)
{
    static uint32_t cnt = 0;
    uint32_t        err_code;
    uint16_t        heart_rate;
    
    UNUSED_PARAMETER(p_context);

    heart_rate = (uint16_t)ble_sensorsim_measure(&m_heart_rate_sim_state, &m_heart_rate_sim_cfg);

    cnt++;
    err_code = ble_hrs_heart_rate_measurement_send(&m_hrs, heart_rate);
    if (
        (err_code != NRF_SUCCESS)
        &&
        (err_code != NRF_ERROR_INVALID_STATE)
        &&
        (err_code != BLE_ERROR_NO_TX_BUFFERS)
        &&
        (err_code != BLE_ERROR_GATTS_SYS_ATTR_MISSING)
    )
    {
        APP_ERROR_HANDLER(err_code);
    }
    
    // Disable RR Interval recording every third heart rate measurement.
    // NOTE: An application will normally not do this. It is done here just for testing generation
    //       of messages without RR Interval measurements.
    m_rr_interval_enabled = ((cnt % 3) != 0);
}


/**@brief RR interval timer timeout handler.
 *
 * @details This function will be called each time the RR interval timer expires.
 *
 * @param[in]   p_context   Pointer used for passing some arbitrary information (context) from the
 *                          app_start_timer() call to the timeout handler.
 */
static void rr_interval_timeout_handler(void * p_context)
{
    UNUSED_PARAMETER(p_context);

    if (m_rr_interval_enabled)
    {
        uint16_t rr_interval;
        
        rr_interval = (uint16_t)ble_sensorsim_measure(&m_rr_interval_sim_state,
                                                      &m_rr_interval_sim_cfg);
        ble_hrs_rr_interval_add(&m_hrs, rr_interval);
    }
}


/**@brief Sensor Contact Detected timer timeout handler.
 *
 * @details This function will be called each time the Sensor Contact Detected timer expires.
 *
 * @param[in]   p_context   Pointer used for passing some arbitrary information (context) from the
 *                          app_start_timer() call to the timeout handler.
 */
static void sensor_contact_detected_timeout_handler(void * p_context)
{
    static bool sensor_contact_detected = false;
    
    UNUSED_PARAMETER(p_context);

    sensor_contact_detected = !sensor_contact_detected;
    ble_hrs_sensor_contact_detected_update(&m_hrs, sensor_contact_detected);
}


/**@brief GAP initialization.
 *
 * @details This function shall be used to setup all the necessary GAP (Generic Access Profile)
 *          parameters of the device. It also sets the permissions and appearance.
 */
static void gap_params_init(void)
{
    uint32_t                err_code;
    ble_gap_conn_params_t   gap_conn_params;
    ble_gap_conn_sec_mode_t sec_mode;

    BLE_GAP_CONN_SEC_MODE_SET_OPEN(&sec_mode);
    
    err_code = sd_ble_gap_device_name_set(&sec_mode, DEVICE_NAME, strlen(DEVICE_NAME));
    APP_ERROR_CHECK(err_code);

    err_code = sd_ble_gap_appearance_set(BLE_APPEARANCE_HEART_RATE_SENSOR_HEART_RATE_BELT);
    APP_ERROR_CHECK(err_code);
    
    memset(&gap_conn_params, 0, sizeof(gap_conn_params));

    gap_conn_params.min_conn_interval = MIN_CONN_INTERVAL;
    gap_conn_params.max_conn_interval = MAX_CONN_INTERVAL;
    gap_conn_params.slave_latency     = SLAVE_LATENCY;
    gap_conn_params.conn_sup_timeout  = CONN_SUP_TIMEOUT;

    err_code = sd_ble_gap_ppcp_set(&gap_conn_params);
    APP_ERROR_CHECK(err_code);
}


/**@brief Advertising functionality initialization.
 *
 * @details Encodes the required advertising data and passes it to the stack.
 *          Also builds a structure to be passed to the stack when starting advertising.
 */
static void advertising_init(void)
{
    uint32_t      err_code;
    ble_advdata_t advdata;
    uint8_t       flags = BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE;
    
    ble_uuid_t adv_uuids[] = 
    {
        {BLE_UUID_HEART_RATE_SERVICE,         BLE_UUID_TYPE_BLE}, 
        {BLE_UUID_BATTERY_SERVICE,            BLE_UUID_TYPE_BLE}, 
        {BLE_UUID_DEVICE_INFORMATION_SERVICE, BLE_UUID_TYPE_BLE}
    };

    // Build and set advertising data
    memset(&advdata, 0, sizeof(advdata));
    
    advdata.name_type               = BLE_ADVDATA_FULL_NAME;
    advdata.include_appearance      = true;
    advdata.flags.size              = sizeof(flags);
    advdata.flags.p_data            = &flags;
    advdata.uuids_complete.uuid_cnt = sizeof(adv_uuids) / sizeof(adv_uuids[0]);
    advdata.uuids_complete.p_uuids  = adv_uuids;
    
    err_code = ble_advdata_set(&advdata, NULL);
    APP_ERROR_CHECK(err_code);

    // Initialise advertising parameters (used when starting advertising)
    memset(&m_adv_params, 0, sizeof(m_adv_params));
    
    m_adv_params.type         = BLE_GAP_ADV_TYPE_ADV_IND;
    m_adv_params.p_peer_addr  = NULL;                           // Undirected advertisement
    m_adv_params.fp           = BLE_GAP_ADV_FP_ANY;
    m_adv_params.interval     = APP_ADV_INTERVAL;
    m_adv_params.timeout      = APP_ADV_TIMEOUT_IN_SECONDS;
}


/**@brief Initialize services that will be used by the application.
 *
 * @details Initialize the Heart Rate, Battery and Device Information services.
 */
static void services_init(void)
{
    uint32_t       err_code;
    ble_hrs_init_t hrs_init;
    ble_bas_init_t bas_init;
    ble_dis_init_t dis_init;
    uint8_t        body_sensor_location;
    
    // Initialize Heart Rate Service
    body_sensor_location = BLE_HRS_BODY_SENSOR_LOCATION_FINGER;
    
    memset(&hrs_init, 0, sizeof(hrs_init));
    
    hrs_init.is_sensor_contact_supported = true;
    hrs_init.p_body_sensor_location      = &body_sensor_location;

    // Here the sec level for the Heart Rate Service can be changed/increased.
    BLE_GAP_CONN_SEC_MODE_SET_OPEN(&hrs_init.hrs_hrm_attr_md.cccd_write_perm);
    BLE_GAP_CONN_SEC_MODE_SET_NO_ACCESS(&hrs_init.hrs_hrm_attr_md.read_perm);
    BLE_GAP_CONN_SEC_MODE_SET_NO_ACCESS(&hrs_init.hrs_hrm_attr_md.write_perm);

    BLE_GAP_CONN_SEC_MODE_SET_OPEN(&hrs_init.hrs_bsl_attr_md.read_perm);
    BLE_GAP_CONN_SEC_MODE_SET_NO_ACCESS(&hrs_init.hrs_bsl_attr_md.write_perm);

    err_code = ble_hrs_init(&m_hrs, &hrs_init);
    APP_ERROR_CHECK(err_code);
    
    // Initialize Battery Service
    memset(&bas_init, 0, sizeof(bas_init));
    
    // Here the sec level for the Battery Service can be increased.
    BLE_GAP_CONN_SEC_MODE_SET_OPEN(&bas_init.battery_level_char_attr_md.cccd_write_perm);
    BLE_GAP_CONN_SEC_MODE_SET_OPEN(&bas_init.battery_level_char_attr_md.read_perm);
    BLE_GAP_CONN_SEC_MODE_SET_NO_ACCESS(&bas_init.battery_level_char_attr_md.write_perm);

    BLE_GAP_CONN_SEC_MODE_SET_OPEN(&bas_init.battery_level_report_read_perm);

    bas_init.evt_handler          = NULL;
    bas_init.support_notification = true;
    bas_init.p_report_ref         = NULL;
    bas_init.initial_batt_level   = 100;

    err_code = ble_bas_init(&m_bas, &bas_init);
    APP_ERROR_CHECK(err_code);

    // Initialize Device Information Service
    memset(&dis_init, 0, sizeof(dis_init));
    
    ble_srv_ascii_to_utf8(&dis_init.manufact_name_str, MANUFACTURER_NAME);

    BLE_GAP_CONN_SEC_MODE_SET_OPEN(&dis_init.dis_attr_md.read_perm);
    BLE_GAP_CONN_SEC_MODE_SET_NO_ACCESS(&dis_init.dis_attr_md.write_perm);

    err_code = ble_dis_init(&dis_init);
    APP_ERROR_CHECK(err_code);
}


/**@brief Initialize the sensor simulators.
 */
static void sensor_sim_init(void)
{
    m_battery_sim_cfg.min          = MIN_BATTERY_LEVEL;
    m_battery_sim_cfg.max          = MAX_BATTERY_LEVEL;
    m_battery_sim_cfg.incr         = BATTERY_LEVEL_INCREMENT;
    m_battery_sim_cfg.start_at_max = true;
    
    ble_sensorsim_init(&m_battery_sim_state, &m_battery_sim_cfg);
    
    m_heart_rate_sim_cfg.min          = MIN_HEART_RATE;
    m_heart_rate_sim_cfg.max          = MAX_HEART_RATE;
    m_heart_rate_sim_cfg.incr         = HEART_RATE_INCREMENT;
    m_heart_rate_sim_cfg.start_at_max = false;
    
    ble_sensorsim_init(&m_heart_rate_sim_state, &m_heart_rate_sim_cfg);
    
    m_rr_interval_sim_cfg.min          = MIN_RR_INTERVAL;
    m_rr_interval_sim_cfg.max          = MAX_RR_INTERVAL;
    m_rr_interval_sim_cfg.incr         = RR_INTERVAL_INCREMENT;
    m_rr_interval_sim_cfg.start_at_max = false;
    
    ble_sensorsim_init(&m_rr_interval_sim_state, &m_rr_interval_sim_cfg);
}


/**@brief Initialize security parameters.
 */
static void sec_params_init(void)
{
    m_sec_params.timeout      = SEC_PARAM_TIMEOUT;
    m_sec_params.bond         = SEC_PARAM_BOND;
    m_sec_params.mitm         = SEC_PARAM_MITM;
    m_sec_params.io_caps      = SEC_PARAM_IO_CAPABILITIES;
    m_sec_params.oob          = SEC_PARAM_OOB;  
    m_sec_params.min_key_size = SEC_PARAM_MIN_KEY_SIZE;
    m_sec_params.max_key_size = SEC_PARAM_MAX_KEY_SIZE;
}


/**@brief Start application timers.
 */
static void application_timers_start(void)
{
    uint32_t err_code;
    
    // Create timers
    err_code = app_timer_create(&m_battery_timer_id,
                                APP_TIMER_MODE_REPEATED,
                                battery_level_meas_timeout_handler);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&m_heart_rate_timer_id,
                                APP_TIMER_MODE_REPEATED,
                                heart_rate_meas_timeout_handler);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&m_rr_interval_timer_id,
                                APP_TIMER_MODE_REPEATED,
                                rr_interval_timeout_handler);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&m_sensor_contact_timer_id,
                                APP_TIMER_MODE_REPEATED,
                                sensor_contact_detected_timeout_handler);
    APP_ERROR_CHECK(err_code);
    
    // Start timers
    err_code = app_timer_start(m_battery_timer_id, BATTERY_LEVEL_MEAS_INTERVAL, NULL);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_start(m_heart_rate_timer_id, HEART_RATE_MEAS_INTERVAL, NULL);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_start(m_rr_interval_timer_id, RR_INTERVAL_INTERVAL, NULL);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_start(m_sensor_contact_timer_id, SENSOR_CONTACT_DETECTED_INTERVAL, NULL);
    APP_ERROR_CHECK(err_code);
}


/**@brief Start advertising.
 */
static void advertising_start(void)
{
    uint32_t err_code;
    
    err_code = sd_ble_gap_adv_start(&m_adv_params);
    APP_ERROR_CHECK(err_code);
    
    nrf_gpio_pin_set(ADVERTISING_LED_PIN_NO);
}


/**@brief Connection Parameters module error handler.
 *
 * @param[in]   nrf_error   Error code containing information about what went wrong.
 */
static void conn_params_error_handler(uint32_t nrf_error)
{
    APP_ERROR_HANDLER(nrf_error);
}


/**@brief Initialize the Connection Parameters module.
 */
static void conn_params_init(void)
{
    uint32_t               err_code;
    ble_conn_params_init_t cp_init;
    
    memset(&cp_init, 0, sizeof(cp_init));

    cp_init.p_conn_params                  = NULL;
    cp_init.first_conn_params_update_delay = FIRST_CONN_PARAMS_UPDATE_DELAY;
    cp_init.next_conn_params_update_delay  = NEXT_CONN_PARAMS_UPDATE_DELAY;
    cp_init.max_conn_params_update_count   = MAX_CONN_PARAMS_UPDATE_COUNT;
    cp_init.start_on_notify_cccd_handle    = m_hrs.hrm_handles.cccd_handle;
    cp_init.disconnect_on_fail             = true;
    cp_init.evt_handler                    = NULL;
    cp_init.error_handler                  = conn_params_error_handler;
    
    err_code = ble_conn_params_init(&cp_init);
    APP_ERROR_CHECK(err_code);
}


/**@brief Application's BLE Stack event handler.
 *
 * @param[in]   p_ble_evt   Bluetooth stack event.
 */
static void on_ble_evt(ble_evt_t * p_ble_evt)
{
    uint32_t                         err_code = NRF_SUCCESS;
    static uint16_t                  m_conn_handle = BLE_CONN_HANDLE_INVALID;
    static ble_gap_evt_auth_status_t m_auth_status;
    ble_gap_enc_info_t *             p_enc_info;

    switch (p_ble_evt->header.evt_id)
    {
        case BLE_GAP_EVT_CONNECTED:
            nrf_gpio_pin_set(CONNECTED_LED_PIN_NO);
            nrf_gpio_pin_clear(ADVERTISING_LED_PIN_NO);
            m_conn_handle = p_ble_evt->evt.gap_evt.conn_handle;
            break;
            
        case BLE_GAP_EVT_DISCONNECTED:
            nrf_gpio_pin_clear(CONNECTED_LED_PIN_NO);
            m_conn_handle = BLE_CONN_HANDLE_INVALID;
            advertising_start();
            break;

        case BLE_GAP_EVT_SEC_PARAMS_REQUEST:
            err_code = sd_ble_gap_sec_params_reply(m_conn_handle, 
                                                   BLE_GAP_SEC_STATUS_SUCCESS, 
                                                   &m_sec_params);
            break;
            
        case BLE_GAP_EVT_AUTH_STATUS:
            m_auth_status = p_ble_evt->evt.gap_evt.params.auth_status;
            break;

        case BLE_GATTS_EVT_SYS_ATTR_MISSING:
            err_code = sd_ble_gatts_sys_attr_set(m_conn_handle, NULL, 0);
            break;

        case BLE_GAP_EVT_SEC_INFO_REQUEST:
            p_enc_info = &m_auth_status.periph_keys.enc_info;
            if (p_enc_info->div == p_ble_evt->evt.gap_evt.params.sec_info_request.div)
            {
                err_code = sd_ble_gap_sec_info_reply(m_conn_handle, p_enc_info, NULL);
            }
            else
            {
                // No keys found for this device
                err_code = sd_ble_gap_sec_info_reply(m_conn_handle, NULL, NULL);
            }
            break;

        case BLE_GAP_EVT_TIMEOUT:
            if (p_ble_evt->evt.gap_evt.params.timeout.src == BLE_GAP_TIMEOUT_SRC_ADVERTISEMENT)
            { 
                nrf_gpio_pin_clear(ADVERTISING_LED_PIN_NO);
                
                err_code = app_button_disable();
                if (err_code == NRF_SUCCESS)
                {
                    GPIO_WAKEUP_BUTTON_CONFIG(BLE_BUTTON_PIN_NO);
                    GPIO_WAKEUP_BUTTON_CONFIG(GZLL_BUTTON_PIN_NO);

                    // Go to system-off mode
                    // (this function will not return; wakeup will cause a reset)
                    err_code = sd_power_system_off();
                }  
            }
            break;
            
        default: 
            break;
    }
    
    APP_ERROR_CHECK(err_code);
}


/**@brief Dispatches a BLE stack event to all modules with a BLE stack event handler.
 *
 * @details This function is called from the BLE Stack event interrupt handler after a BLE stack
 *          event has been received.
 *
 * @param[in]   p_ble_evt   Bluetooth stack event.
 */
static void ble_evt_dispatch(ble_evt_t * p_ble_evt)
{
    ble_hrs_on_ble_evt(&m_hrs, p_ble_evt);
    ble_bas_on_ble_evt(&m_bas, p_ble_evt);
    ble_conn_params_on_ble_evt(p_ble_evt);
    on_ble_evt(p_ble_evt);
}


void ble_stack_start(void)
{
    BLE_STACK_HANDLER_INIT(NRF_CLOCK_LFCLKSRC_XTAL_20_PPM,
                           BLE_L2CAP_MTU_DEF,
                           ble_evt_dispatch,
                           false);
}


void ble_stack_stop(void)
{
    uint32_t err_code;
    
    err_code = sd_softdevice_disable();
    APP_ERROR_CHECK(err_code);
}


void ble_hrs_app_start(void)
{
    gap_params_init();
    advertising_init();
    services_init();
    sensor_sim_init();
    conn_params_init();
    application_timers_start();
    sec_params_init();
    advertising_start();
}


void ble_hrs_app_stop(void)
{
    uint32_t err_code;
    
    // Stop any impending connection parameters update.
    err_code = ble_conn_params_stop();
    APP_ERROR_CHECK(err_code);
    
    // Stop application timers
    err_code = app_timer_stop(m_battery_timer_id);
    APP_ERROR_CHECK(err_code);
    err_code = app_timer_stop(m_heart_rate_timer_id);
    APP_ERROR_CHECK(err_code);
    err_code = app_timer_stop(m_rr_interval_timer_id);
    APP_ERROR_CHECK(err_code);
    err_code = app_timer_stop(m_sensor_contact_timer_id);
    APP_ERROR_CHECK(err_code);
    
    err_code = app_button_disable();
    APP_ERROR_CHECK(err_code);
}

/** 
 * @}
 */
