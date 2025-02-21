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
#ifndef NRF6310_H
#define NRF6310_H

#define LED_START      8
#define LED_STOP       15
#define LED_PORT       NRF_GPIO_PORT_SELECT_PORT1
#define LED_OFFSET     0

#define LED0           8
#define LED1           9

#define BUTTON_START   24
#define BUTTON0        24
#define BUTTON_STOP    30
#define BUTTON1        25

#define RX_PIN_NUMBER  5    // UART RX pin number.
#define TX_PIN_NUMBER  6    // UART TX pin number.
#define CTS_PIN_NUMBER 7    // UART Clear To Send pin number. Not used if HWFC is set to false
#define RTS_PIN_NUMBER 8    // Not used if HWFC is set to false
#define HWFC           false // UART hardware flow control

#define BLINKY_STATE_MASK   0x07

#endif
