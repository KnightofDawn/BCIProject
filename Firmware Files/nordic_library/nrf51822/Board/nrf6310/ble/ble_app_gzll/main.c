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
 * @defgroup ble_sdk_app_gzll_main main.c
 * @{
 * @ingroup ble_sdk_app_gzll
 * @brief Multiprotocol Sample Application main file.
 *
 * This file contains the source code for a sample application using both Nordic Gazell proprietary
 * radio protocol and Bluetooth Low Energy radio protocol. In Bluetooth mode, it behave as a Heart 
 * Rate sensor, in Gazell mode it behaves as a 'device'.
 */

#include <stdint.h>
#include <string.h>
#include "nordic_common.h"
#include "nrf.h"
#include "nrf_sdm.h"
#include "app_error.h"
#include "nrf_gpio.h"
#include "ble_app_gzll_device.h"
#include "ble_app_gzll_hr.h"
#include "ble_app_gzll_ui.h"
#include "ble_nrf6310_pins.h"
#include "ble_error_log.h"
#include "app_timer.h"
#include "app_gpiote.h"
#include "ble_app_gzll_common.h"


#define DEAD_BEEF  0xDEADBEEF   /**< Value used as error code on stack dump, can be used to identify stack location on stack unwind. */

volatile bool running_proprietary_mode = false;


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


/**@brief Timer module initialization.
 */
static void timers_init(void)
{
    // Initialize timer module, making it use the scheduler
    APP_TIMER_INIT(APP_TIMER_PRESCALER, APP_TIMER_MAX_TIMERS, APP_TIMER_OP_QUEUE_SIZE, false);
}


/**@brief Initialize GPIOTE handler module.
 */
static void gpiote_init(void)
{
    APP_GPIOTE_INIT(APP_GPIOTE_MAX_USERS);
}


/**@brief Power Management.
 */
static void power_manage(void)
{
    if (running_proprietary_mode)
    {
        // Use directly __WFE and __SEV macros since the SoftDevice is not available in proprietary mode
        // Wait for event
        __WFE();

        // Clear Event Register
        __SEV();
        __WFE();
    }
    else
    {
        uint32_t  err_code;
        
        // Use SoftDevice API for power_management when in Bluetooth Mode
        err_code = sd_app_event_wait();
        APP_ERROR_CHECK(err_code);
    }

}


/**@brief Application main function.
 */
int main(void)
{
    bool previous_mode = running_proprietary_mode;
    
    leds_init();
    ble_stack_start();
    timers_init();
    gpiote_init();
    buttons_init();
    ble_hrs_app_start();
    
    // Enter main loop
    for (;;)
    {
        power_manage();
        if (running_proprietary_mode != previous_mode)
        {
            previous_mode = running_proprietary_mode;
            if (running_proprietary_mode)
            {
                // Stop all heart rate functionality before disabling the SoftDevice
                ble_hrs_app_stop();
                
                // Disable the S110 stack
                ble_stack_stop();
                nrf_gpio_pin_clear(ADVERTISING_LED_PIN_NO);
                nrf_gpio_pin_clear(CONNECTED_LED_PIN_NO  );
                
                // Enable Gazell
                gzll_app_start();
                timers_init();
                gpiote_init();
                buttons_init();
            }
            else
            {
                // Disable Gazell
                gzll_app_stop();
                nrf_gpio_pin_clear(GZLL_TX_SUCCESS_LED_PIN_NO);
                nrf_gpio_pin_clear(GZLL_TX_FAIL_LED_PIN_NO   );
                
                // Re-enable the S110 stack
                ble_stack_start();
                timers_init();
                gpiote_init();
                buttons_init();
                ble_hrs_app_start();
            }
        }
    }
}

/** 
 * @}
 */
