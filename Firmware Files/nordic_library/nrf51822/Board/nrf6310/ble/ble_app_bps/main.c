/* Copyright (c) 2012 Nordic Semiconductor. All Rights Reserved.
 *
 * The information contained herein is confidential property of Nordic
 * Semiconductor ASA.Terms and conditions of usage are described in detail
 * in NORDIC SEMICONDUCTOR STANDARD SOFTWARE LICENSE AGREEMENT.
 *
 * Licensees are granted free, non-transferable use of the information. NO
 * WARRANTY of ANY KIND is provided. This heading must NOT be removed from
 * the file.
 *
 * $$
 */

/** @file
 *
 * @defgroup ble_sdk_app_bps_main main.c
 * @{
 * @ingroup ble_sdk_app_bps
 * @brief Blood Pressure Service Sample Application main file.
 *
 * This file contains the source code for a sample application using the Blood Pressure service
 * It also includes the sample code for Battery and Device Information services.
 * This application uses the @ref srvlib_conn_params module.
 */

#include <stdint.h>
#include <string.h>
#include "ble_bondmngr.h"
#include "nordic_common.h"
#include "nrf.h"
#include "app_error.h"
#include "nrf_gpio.h"
#include "nrf51_bitfields.h"
#include "ble.h"
#include "ble_hci.h"
#include "ble_srv_common.h"
#include "ble_advdata.h"
#include "ble_bas.h"
#include "ble_bps.h"
#include "ble_dis.h"
#include "ble_conn_params.h"
#include "ble_nrf6310_pins.h"
#include "ble_sensorsim.h"
#include "ble_stack_handler.h"
#include "app_timer.h"
#include "app_gpiote.h"
#include "app_button.h"
#include "ble_error_log.h"
#include "ble_radio_notification.h"
#include "ble_flash.h"


#define SEND_MEAS_BUTTON_PIN_NO              NRF6310_BUTTON_0                           /**< Button used for sending a measurement. */
#define BONDMNGR_DELETE_BUTTON_PIN_NO        NRF6310_BUTTON_1                           /**< Button used for deleting all bonded masters during startup. */

#define DEVICE_NAME                          "Nordic_BPS"                               /**< Name of device. Will be included in the advertising data. */
#define MANUFACTURER_NAME                    "NordicSemiconductor"                      /**< Manufacturer. Will be passed to Device Information Service. */
#define MODEL_NUM                            "NS-BPS-EXAMPLE"                           /**< Model number. Will be passed to Device Information Service. */
#define MANUFACTURER_ID                      0x1122334455                               /**< Manufacturer ID, part of System ID. Will be passed to Device Information Service. */
#define ORG_UNIQUE_ID                        0x667788                                   /**< Organizational Unique ID, part of System ID. Will be passed to Device Information Service. */

#define APP_ADV_INTERVAL                     40                                         /**< The advertising interval (in units of 0.625 ms. This value corresponds to 25 ms). */
#define APP_ADV_TIMEOUT_IN_SECONDS           180                                        /**< The advertising timeout in units of seconds. */

#define APP_TIMER_PRESCALER                  0                                          /**< Value of the RTC1 PRESCALER register. */
#define APP_TIMER_MAX_TIMERS                 3                                          /**< Maximum number of simultaneously created timers. */
#define APP_TIMER_OP_QUEUE_SIZE              4                                          /**< Size of timer operation queues. */

#define NUM_SIM_MEAS_VALUES                  4                                          /**< Number of simulated measurements to cycle through. */

#define SIM_MEAS_1_SYSTOLIC                  117                                        /**< Simulated measurement value for systolic pressure. */
#define SIM_MEAS_1_DIASTOLIC                 76                                         /**< Simulated measurement value for diastolic pressure. */
#define SIM_MEAS_1_MEAN_AP                   103                                        /**< Simulated measurement value for mean arterial pressure. */
#define SIM_MEAS_1_PULSE_RATE                60                                         /**< Simulated measurement value for pulse rate. */

#define SIM_MEAS_2_SYSTOLIC                  121                                        /**< Simulated measurement value for systolic pressure. */
#define SIM_MEAS_2_DIASTOLIC                 81                                         /**< Simulated measurement value for diastolic pressure. */
#define SIM_MEAS_2_MEAN_AP                   106                                        /**< Simulated measurement value for mean arterial pressure. */
#define SIM_MEAS_2_PULSE_RATE                72                                         /**< Simulated measurement value for pulse rate. */

#define SIM_MEAS_3_SYSTOLIC                  138                                        /**< Simulated measurement value for systolic pressure. */
#define SIM_MEAS_3_DIASTOLIC                 88                                         /**< Simulated measurement value for diastolic pressure. */
#define SIM_MEAS_3_MEAN_AP                   120                                        /**< Simulated measurement value for mean arterial pressure. */
#define SIM_MEAS_3_PULSE_RATE                105                                        /**< Simulated measurement value for pulse rate. */

#define SIM_MEAS_4_SYSTOLIC                  145                                        /**< Simulated measurement value for systolic pressure. */
#define SIM_MEAS_4_DIASTOLIC                 100                                        /**< Simulated measurement value for diastolic pressure. */
#define SIM_MEAS_4_MEAN_AP                   131                                        /**< Simulated measurement value for mean arterial pressure. */
#define SIM_MEAS_4_PULSE_RATE                125                                        /**< Simulated measurement value for pulse rate. */

#define BATTERY_LEVEL_MEAS_INTERVAL          APP_TIMER_TICKS(2000, APP_TIMER_PRESCALER) /**< Battery level measurement interval (ticks). */
#define MIN_BATTERY_LEVEL                    81                                         /**< Minimum battery level as returned by the simulated measurement function. */
#define MAX_BATTERY_LEVEL                    100                                        /**< Maximum battery level as returned by the simulated measurement function. */
#define BATTERY_LEVEL_INCREMENT              1                                          /**< Value by which the battery level is incremented/decremented for each call to the simulated measurement function. */

#define MIN_CONN_INTERVAL                    ((1 * 800) / 2)                            /**< Minimum acceptable connection interval (0.5 seconds). */
#define MAX_CONN_INTERVAL                    (1 * 800)                                  /**< Maximum acceptable connection interval (1 second). */
#define SLAVE_LATENCY                        0                                          /**< Slave latency. */
#define CONN_SUP_TIMEOUT                     (4 * 100)                                  /**< Connection supervisory timeout (4 seconds). */

#define FIRST_CONN_PARAMS_UPDATE_DELAY       APP_TIMER_TICKS(5000, APP_TIMER_PRESCALER) /**< Time from initiating event (connect or start of indication) to first time sd_ble_gap_conn_param_update is called (5 seconds). */
#define NEXT_CONN_PARAMS_UPDATE_DELAY        APP_TIMER_TICKS(5000, APP_TIMER_PRESCALER) /**< Time between each call to sd_ble_gap_conn_param_update after the first (30 seconds). */
#define MAX_CONN_PARAMS_UPDATE_COUNT         3                                          /**< Number of attempts before giving up the connection parameter negotiation. */

#define APP_GPIOTE_MAX_USERS                 1                                          /**< Maximum number of users of the GPIOTE handler. */

#define BUTTON_DETECTION_DELAY               APP_TIMER_TICKS(50, APP_TIMER_PRESCALER)   /**< Delay from a GPIOTE event until a button is reported as pushed (in number of timer ticks). */

#define SEC_PARAM_TIMEOUT                    30                                         /**< Timeout for Pairing Request or Security Request (in seconds). */
#define SEC_PARAM_BOND                       1                                          /**< Perform bonding. */
#define SEC_PARAM_MITM                       0                                          /**< Man In The Middle protection not required. */
#define SEC_PARAM_IO_CAPABILITIES            BLE_GAP_IO_CAPS_NONE                       /**< No I/O capabilities. */
#define SEC_PARAM_OOB                        0                                          /**< Out Of Band data not available. */
#define SEC_PARAM_MIN_KEY_SIZE               7                                          /**< Minimum encryption key size. */
#define SEC_PARAM_MAX_KEY_SIZE               16                                         /**< Maximum encryption key size. */

#define FLASH_PAGE_SYS_ATTR                  253                                        /**< Flash page used for bond manager system attribute information. */
#define FLASH_PAGE_BOND                      255                                        /**< Flash page used for bond manager bonding information. */

#define DEAD_BEEF                            0xDEADBEEF                                 /**< Value used as error code on stack dump, can be used to identify stack location on stack unwind. */

typedef struct bps_meas_sim_value_s
{
    ieee_float16_t systolic;
    ieee_float16_t diastolic;
    ieee_float16_t mean_arterial;
    ieee_float16_t pulse_rate;
} bps_meas_sim_value_t;

static uint16_t                              m_conn_handle = BLE_CONN_HANDLE_INVALID;   /**< Handle of the current connection. */
static ble_gap_sec_params_t                  m_sec_params;                              /**< Security requirements for this application. */
static ble_gap_adv_params_t                  m_adv_params;                              /**< Parameters to be passed to the stack when starting advertising. */
static ble_bas_t                             m_bas;                                     /**< Structure used to identify the battery service. */
static ble_bps_t                             m_bps;                                     /**< Structure used to identify the blood pressure service. */

static bps_meas_sim_value_t                  m_bps_meas_sim_val[NUM_SIM_MEAS_VALUES];   /**< Blood Pressure simulated measurements. */
static bool                                  m_bps_meas_ind_conf_pending = false;       /**< Flag to keep track of when an indication confirmation is pending. */

static ble_sensorsim_cfg_t                   m_battery_sim_cfg;                         /**< Battery Level sensor simulator configuration. */
static ble_sensorsim_state_t                 m_battery_sim_state;                       /**< Battery Level sensor simulator state. */

static app_timer_id_t                        m_battery_timer_id;                        /**< Battery timer. */


/**@brief Error handler function, which is called when an error has occurred. 
 *
 * @param[in] error_code  Error code supplied to the handler.
 * @param[in] line_num    Line number where the handler is called.
 * @param[in] p_file_name Pointer to the file name. 
 */
void app_error_handler(uint32_t error_code, uint32_t line_num, const uint8_t * p_file_name)
{
    // Copying parameters to static variables because parameters are not accessible in debugger.
    static volatile uint8_t  s_file_name[128];
    static volatile uint16_t s_line_num;
    static volatile uint32_t s_error_code;    
        
    strcpy((char *)s_file_name, (const char *)p_file_name);
    s_line_num   = line_num;
    s_error_code = error_code;
    UNUSED_VARIABLE(s_file_name);
    UNUSED_VARIABLE(s_line_num);
    UNUSED_VARIABLE(s_error_code);    
    
    nrf_gpio_pin_set(ASSERT_LED_PIN_NO);

    (void) ble_error_log_write(DEAD_BEEF, p_file_name, line_num);

    for (;;)
    {
        // Loop forever. On assert, the system can only recover on reset.
    }
}


/**@brief Assert macro callback function.
 *
 * @details This function will be called if the ASSERT macro fails.
 *
 * @param[in]   line_num   Line number of the failing ASSERT call.
 * @param[in]   file_name  File name of the failing ASSERT call.
 */
void assert_nrf_callback(uint16_t line_num, const uint8_t * file_name)
{
    // Copying parameters to static variables because parameters are not accessible in debugger
    static volatile uint8_t  s_file_name[128];
    static volatile uint16_t s_line_num;

    strcpy((char *)s_file_name, (const char *)file_name);
    s_line_num = line_num;
    UNUSED_VARIABLE(s_file_name);
    UNUSED_VARIABLE(s_line_num);
    
    nrf_gpio_pin_set(ASSERT_LED_PIN_NO);

    (void) ble_error_log_write(DEAD_BEEF, file_name, line_num);

    for (;;)
    {
        // Loop forever. On assert, the system can only recover on reset
    }
}


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


/**@brief Populate simulated blood pressure measurement.
 */
static void bps_sim_measurement(ble_bps_meas_t * p_meas)
{
    static ble_date_time_t time_stamp = { 2012, 12, 5, 11, 05, 03 };
    static uint8_t         ndx        = 0;

    p_meas->blood_pressure_units_in_kpa       = false;
    p_meas->time_stamp_present                = (ndx == 0) || (ndx == 2);
    p_meas->pulse_rate_present                = (ndx == 0) || (ndx == 1);
    p_meas->user_id_present                   = false;
    p_meas->measurement_status_present        = false;

    p_meas->blood_pressure_systolic.mantissa  = m_bps_meas_sim_val[ndx].systolic.mantissa;
    p_meas->blood_pressure_systolic.exponent  = m_bps_meas_sim_val[ndx].systolic.exponent;

    p_meas->blood_pressure_diastolic.mantissa = m_bps_meas_sim_val[ndx].diastolic.mantissa;
    p_meas->blood_pressure_diastolic.exponent = m_bps_meas_sim_val[ndx].diastolic.exponent;

    p_meas->mean_arterial_pressure.mantissa   = m_bps_meas_sim_val[ndx].mean_arterial.mantissa;
    p_meas->mean_arterial_pressure.exponent   = m_bps_meas_sim_val[ndx].mean_arterial.exponent;

    p_meas->time_stamp                        = time_stamp;

    p_meas->pulse_rate.mantissa               = m_bps_meas_sim_val[ndx].pulse_rate.mantissa;
    p_meas->pulse_rate.exponent               = m_bps_meas_sim_val[ndx].pulse_rate.exponent;

    // Update index to simluated measurements
    ndx++;
    if (ndx == NUM_SIM_MEAS_VALUES)
    {
        ndx = 0;
    }

    // Update simulated time stamp
    time_stamp.seconds += 27;
    if (time_stamp.seconds > 59)
    {
        time_stamp.seconds -= 60;
        time_stamp.minutes++;
        if (time_stamp.minutes > 59)
        {
            time_stamp.minutes = 0;
        }
    }
}


/**@brief LEDs initialization.
 *
 * @details Initializes all LEDs used by this application.
 */
static void leds_init(void)
{
    GPIO_LED_CONFIG(ADVERTISING_LED_PIN_NO);
    GPIO_LED_CONFIG(CONNECTED_LED_PIN_NO);
    GPIO_LED_CONFIG(ASSERT_LED_PIN_NO);
}


/**@brief Timer initialization.
 *
 * @details Initializes the timer module. This creates and starts application timers.
 */
static void timers_init(void)
{
    uint32_t err_code;
    
    // Initialize timer module
    APP_TIMER_INIT(APP_TIMER_PRESCALER, APP_TIMER_MAX_TIMERS, APP_TIMER_OP_QUEUE_SIZE, false);

    // Create timers
    err_code = app_timer_create(&m_battery_timer_id,
                                APP_TIMER_MODE_REPEATED,
                                battery_level_meas_timeout_handler);
    APP_ERROR_CHECK(err_code);
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

    err_code = sd_ble_gap_appearance_set(BLE_APPEARANCE_GENERIC_BLOOD_PRESSURE);
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
        {BLE_UUID_BLOOD_PRESSURE_SERVICE,     BLE_UUID_TYPE_BLE}, 
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
    
    m_adv_params.type        = BLE_GAP_ADV_TYPE_ADV_IND;
    m_adv_params.p_peer_addr = NULL;                           // Undirected advertisement
    m_adv_params.fp          = BLE_GAP_ADV_FP_ANY;
    m_adv_params.interval    = APP_ADV_INTERVAL;
    m_adv_params.timeout     = APP_ADV_TIMEOUT_IN_SECONDS;
}


/**@brief Simulate and send one Blood Pressure Measurement.
 */
static void blood_pressure_measurement_send(void)
{
    ble_bps_meas_t simulated_meas;
    uint32_t       err_code;

    if (!m_bps_meas_ind_conf_pending)
    {
        bps_sim_measurement(&simulated_meas);
        
        err_code = ble_bps_measurement_send(&m_bps, &simulated_meas);
        switch (err_code)
        {
            case NRF_SUCCESS:
                // Measurement was successfully sent, wait for confirmation
                m_bps_meas_ind_conf_pending = true;
                break;
                
            case NRF_ERROR_INVALID_STATE:
                // Ignore error
                break;
                
            default:
                APP_ERROR_HANDLER(err_code);
        }
    }
}


/**@brief Blood Pressure Service event handler.
 *
 * @details This function will be called for all Blood Pressure Service events which are passed to
 *          the application.
 *
 * @param[in]   p_bps   Blood Pressure Service stucture.
 * @param[in]   p_evt   Event received from the Blood Pressure Service.
 */
static void on_bps_evt(ble_bps_t * p_bps, ble_bps_evt_t *p_evt)
{
    switch (p_evt->evt_type)
    {
        case BLE_BPS_EVT_INDICATION_ENABLED:
            // Indication has been enabled, send a single blood pressure measurement
            blood_pressure_measurement_send();
            break;
            
        case BLE_BPS_EVT_INDICATION_CONFIRMED:
            m_bps_meas_ind_conf_pending = false;
            break;

        default:
            break;
    }
}


/**@brief Initialize services that will be used by the application.
 *
 * @details Initialize the Blood Pressure, Battery and Device Information services.
 */
static void services_init(void)
{
    uint32_t         err_code;
    ble_bps_init_t   bps_init;
    ble_bas_init_t   bas_init;
    ble_dis_init_t   dis_init;
    ble_dis_sys_id_t sys_id;
    
    // Initialize Blood Pressure Service
    memset(&bps_init, 0, sizeof(bps_init));
    
    bps_init.evt_handler = on_bps_evt;
    bps_init.feature     = BLE_BPS_FEATURE_BODY_MOVEMENT_BIT |
                           BLE_BPS_FEATURE_MEASUREMENT_POSITION_BIT;

    // Here the sec level for the Blood Pressure Service can be changed/increased.
    BLE_GAP_CONN_SEC_MODE_SET_ENC_NO_MITM(&bps_init.bps_meas_attr_md.cccd_write_perm);
    BLE_GAP_CONN_SEC_MODE_SET_NO_ACCESS(&bps_init.bps_meas_attr_md.read_perm);
    BLE_GAP_CONN_SEC_MODE_SET_NO_ACCESS(&bps_init.bps_meas_attr_md.write_perm);

    BLE_GAP_CONN_SEC_MODE_SET_OPEN(&bps_init.bps_feature_attr_md.read_perm);
    BLE_GAP_CONN_SEC_MODE_SET_NO_ACCESS(&bps_init.bps_feature_attr_md.write_perm);
    
    err_code = ble_bps_init(&m_bps, &bps_init);
    APP_ERROR_CHECK(err_code);
    
    // Initialize Battery Service
    memset(&bas_init, 0, sizeof(bas_init));
    
    // Here the sec level for the Battery Service can be changed/increased.
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
    ble_srv_ascii_to_utf8(&dis_init.model_num_str,     MODEL_NUM);

    sys_id.manufacturer_id            = MANUFACTURER_ID;
    sys_id.organizationally_unique_id = ORG_UNIQUE_ID;
    dis_init.p_sys_id                 = &sys_id;
    
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
    
    // Simulated measurement #1
    m_bps_meas_sim_val[0].systolic.mantissa       = SIM_MEAS_1_SYSTOLIC;
    m_bps_meas_sim_val[0].systolic.exponent       = 0;
    m_bps_meas_sim_val[0].diastolic.mantissa      = SIM_MEAS_1_DIASTOLIC;
    m_bps_meas_sim_val[0].diastolic.exponent      = 0;
    m_bps_meas_sim_val[0].mean_arterial.mantissa  = SIM_MEAS_1_MEAN_AP;
    m_bps_meas_sim_val[0].mean_arterial.exponent  = 0;
    m_bps_meas_sim_val[0].pulse_rate.mantissa     = SIM_MEAS_1_PULSE_RATE;
    m_bps_meas_sim_val[0].pulse_rate.exponent     = 0;

    // Simulated measurement #2
    m_bps_meas_sim_val[1].systolic.mantissa       = SIM_MEAS_2_SYSTOLIC;
    m_bps_meas_sim_val[1].systolic.exponent       = 0;
    m_bps_meas_sim_val[1].diastolic.mantissa      = SIM_MEAS_2_DIASTOLIC;
    m_bps_meas_sim_val[1].diastolic.exponent      = 0;
    m_bps_meas_sim_val[1].mean_arterial.mantissa  = SIM_MEAS_2_MEAN_AP;
    m_bps_meas_sim_val[1].mean_arterial.exponent  = 0;
    m_bps_meas_sim_val[1].pulse_rate.mantissa     = SIM_MEAS_2_PULSE_RATE;
    m_bps_meas_sim_val[1].pulse_rate.exponent     = 0;

    // Simulated measurement #3
    m_bps_meas_sim_val[2].systolic.mantissa       = SIM_MEAS_3_SYSTOLIC;
    m_bps_meas_sim_val[2].systolic.exponent       = 0;
    m_bps_meas_sim_val[2].diastolic.mantissa      = SIM_MEAS_3_DIASTOLIC;
    m_bps_meas_sim_val[2].diastolic.exponent      = 0;
    m_bps_meas_sim_val[2].mean_arterial.mantissa  = SIM_MEAS_3_MEAN_AP;
    m_bps_meas_sim_val[2].mean_arterial.exponent  = 0;
    m_bps_meas_sim_val[2].pulse_rate.mantissa     = SIM_MEAS_3_PULSE_RATE;
    m_bps_meas_sim_val[2].pulse_rate.exponent     = 0;

    // Simulated measurement #4
    m_bps_meas_sim_val[3].systolic.mantissa       = SIM_MEAS_4_SYSTOLIC;
    m_bps_meas_sim_val[3].systolic.exponent       = 0;
    m_bps_meas_sim_val[3].diastolic.mantissa      = SIM_MEAS_4_DIASTOLIC;
    m_bps_meas_sim_val[3].diastolic.exponent      = 0;
    m_bps_meas_sim_val[3].mean_arterial.mantissa  = SIM_MEAS_4_MEAN_AP;
    m_bps_meas_sim_val[3].mean_arterial.exponent  = 0;
    m_bps_meas_sim_val[3].pulse_rate.mantissa     = SIM_MEAS_4_PULSE_RATE;
    m_bps_meas_sim_val[3].pulse_rate.exponent     = 0;
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

    // Start application timers
    err_code = app_timer_start(m_battery_timer_id, BATTERY_LEVEL_MEAS_INTERVAL, NULL);
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


/**@brief Connection Parameters Module handler.
 *
 * @details This function will be called for all events in the Connection Parameters Module which
 *          are passed to the application.
 *          @note All this function does is to disconnect. This could have been done by simply
 *                setting the disconnect_on_fail config parameter, but instead we use the event
 *                handler mechanism to demonstrate its use.
 *
 * @param[in]   p_evt   Event received from the Connection Parameters Module.
 */
static void on_conn_params_evt(ble_conn_params_evt_t * p_evt)
{
    uint32_t err_code;
    
    APP_ERROR_CHECK_BOOL(p_evt->evt_type == BLE_CONN_PARAMS_EVT_FAILED);
    
    err_code = sd_ble_gap_disconnect(m_conn_handle, BLE_HCI_CONN_INTERVAL_UNACCEPTABLE);
    APP_ERROR_CHECK(err_code);
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
    cp_init.start_on_notify_cccd_handle    = m_bps.meas_handles.cccd_handle;
    cp_init.disconnect_on_fail             = false;
    cp_init.evt_handler                    = on_conn_params_evt;
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
    uint32_t err_code = NRF_SUCCESS;

    switch (p_ble_evt->header.evt_id)
    {
        case BLE_GAP_EVT_CONNECTED:
            nrf_gpio_pin_set(CONNECTED_LED_PIN_NO);
            nrf_gpio_pin_clear(ADVERTISING_LED_PIN_NO);
            // Start detecting button presses
            err_code = app_button_enable();
            m_conn_handle = p_ble_evt->evt.gap_evt.conn_handle;
            break;
            
        case BLE_GAP_EVT_DISCONNECTED:
            nrf_gpio_pin_clear(CONNECTED_LED_PIN_NO);
            
            m_conn_handle               = BLE_CONN_HANDLE_INVALID;
            m_bps_meas_ind_conf_pending = false;

            // Stop detecting button presses when not connected
            err_code = app_button_disable();
            APP_ERROR_CHECK(err_code);

            // Since we are not in a connection and have not started advertising, store bonds
            err_code = ble_bondmngr_bonded_masters_store();
            APP_ERROR_CHECK(err_code);

            advertising_start();
            break;

        case BLE_GAP_EVT_SEC_PARAMS_REQUEST:
            err_code = sd_ble_gap_sec_params_reply(m_conn_handle, 
                                                   BLE_GAP_SEC_STATUS_SUCCESS, 
                                                   &m_sec_params);
            break;

        case BLE_GAP_EVT_TIMEOUT:
            if (p_ble_evt->evt.gap_evt.params.timeout.src == BLE_GAP_TIMEOUT_SRC_ADVERTISEMENT)
            {
                nrf_gpio_pin_clear(ADVERTISING_LED_PIN_NO);

                // Go to system-off mode (this function will not return; wakeup will cause a reset)
                GPIO_WAKEUP_BUTTON_CONFIG(SEND_MEAS_BUTTON_PIN_NO);
                err_code = sd_power_system_off();    
            }
            break;

        case BLE_GATTS_EVT_TIMEOUT:
            if (p_ble_evt->evt.gatts_evt.params.timeout.src == BLE_GATT_TIMEOUT_SRC_PROTOCOL)
            {
                err_code = sd_ble_gap_disconnect(m_conn_handle,
                                                 BLE_HCI_REMOTE_USER_TERMINATED_CONNECTION);
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
    ble_bps_on_ble_evt(&m_bps, p_ble_evt);
    ble_bas_on_ble_evt(&m_bas, p_ble_evt);
    ble_conn_params_on_ble_evt(p_ble_evt);
    ble_bondmngr_on_ble_evt(p_ble_evt);
    on_ble_evt(p_ble_evt);
}


/**@brief BLE stack initialization.
 *
 * @details Initializes the SoftDevice and the BLE event interrupt.
 */
static void ble_stack_init(void)
{
    BLE_STACK_HANDLER_INIT(NRF_CLOCK_LFCLKSRC_XTAL_20_PPM,
                           BLE_L2CAP_MTU_DEF,
                           ble_evt_dispatch,
                           false);
}


/**@brief Button event handler.
 *
 * @param[in]   pin_no   The pin number of the button pressed.
 */
static void button_event_handler(uint8_t pin_no)
{
    switch (pin_no)
    {
        case SEND_MEAS_BUTTON_PIN_NO:
            blood_pressure_measurement_send();
            break;
            
        default:
            APP_ERROR_HANDLER(pin_no);
    }
}


/**@brief Initialize GPIOTE handler module.
 */
static void gpiote_init(void)
{
    APP_GPIOTE_INIT(APP_GPIOTE_MAX_USERS);
}


/**@brief Initialize button handler module.
 */
static void buttons_init(void)
{
    static app_button_cfg_t buttons[] =
    {
        {SEND_MEAS_BUTTON_PIN_NO,       false, NRF_GPIO_PIN_NOPULL, button_event_handler},
        {BONDMNGR_DELETE_BUTTON_PIN_NO, false, NRF_GPIO_PIN_NOPULL, NULL}
    };
    
    APP_BUTTON_INIT(buttons, sizeof(buttons) / sizeof(buttons[0]), BUTTON_DETECTION_DELAY, false);
}


/**@brief Bond Manager module error handler.
 *
 * @param[in]   nrf_error   Error code containing information about what went wrong.
 */
static void bond_manager_error_handler(uint32_t nrf_error)
{
    APP_ERROR_HANDLER(nrf_error);
}


/**@brief Bond Manager module event handler.
 *
 * @param[in]   p_evt   Data associated to the bond manager event.
 */
static void bond_evt_handler(ble_bondmngr_evt_t * p_evt)
{
    uint32_t err_code;
    bool     is_indication_enabled;
    
    switch (p_evt->evt_type)
    {
        case BLE_BONDMNGR_EVT_ENCRYPTED:
            break;

        case BLE_BONDMNGR_EVT_CONN_TO_BONDED_MASTER:
            // Send a single blood pressure measurement if indication is enabled.
            // NOTE: For this to work, make sure ble_bps_on_ble_evt() is called before
            //       ble_bondmngr_on_ble_evt() in ble_evt_dispatch().
            err_code = ble_bps_is_indication_enabled(&m_bps, &is_indication_enabled);
            APP_ERROR_CHECK(err_code);
            if (is_indication_enabled)
            {
                blood_pressure_measurement_send();
            }
            break;
            
        default:
            break;
    }
}


/**@brief Bond Manager initialization.
 */
static void bond_manager_init(void)
{
    uint32_t            err_code;
    ble_bondmngr_init_t bond_init_data;
    bool                bonds_delete;

    // Clear all bonded masters if the Bonds Delete button is pushed
    err_code = app_button_is_pushed(BONDMNGR_DELETE_BUTTON_PIN_NO, &bonds_delete);
    APP_ERROR_CHECK(err_code);

    // Initialize the Bond Manager
    bond_init_data.flash_page_num_bond     = FLASH_PAGE_BOND;
    bond_init_data.flash_page_num_sys_attr = FLASH_PAGE_SYS_ATTR;
    bond_init_data.evt_handler             = bond_evt_handler;
    bond_init_data.error_handler           = bond_manager_error_handler;
    bond_init_data.bonds_delete            = bonds_delete;

    err_code = ble_bondmngr_init(&bond_init_data);
    APP_ERROR_CHECK(err_code);
}


/**@brief Initialize Radio Notification event handler.
 */
static void radio_notification_init(void)
{
    uint32_t err_code;

    err_code = ble_radio_notification_init(NRF_APP_PRIORITY_HIGH,
                                           NRF_RADIO_NOTIFICATION_DISTANCE_4560US,
                                           ble_flash_on_radio_active_evt);
    APP_ERROR_CHECK(err_code);
}


/**@brief Power manager.
 */
static void power_manage(void)
{
    uint32_t err_code = sd_app_event_wait();
    APP_ERROR_CHECK(err_code);
}


/**@brief Application main function.
 */
int main(void)
{
    // Initialize
    leds_init();
    timers_init();
    gpiote_init();
    buttons_init();
    ble_stack_init();
    bond_manager_init();
    gap_params_init();
    advertising_init();
    services_init();
    sensor_sim_init();
    conn_params_init();
    sec_params_init();
    radio_notification_init();

    // Start execution
    application_timers_start();
    advertising_start();

    // Enter main loop
    for (;;)
    {
        power_manage();
    }
}

/** 
 * @}
 */
