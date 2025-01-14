/* Copyright (c) 2013 Nordic Semiconductor. All Rights Reserved.
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

#include "app_uart.h"
#include "app_fifo.h"
#include "nrf.h"
#include "nrf_gpio.h"
#include "app_error.h"
#include "nrf_error.h"
#include "app_util.h"
#include "app_gpiote.h"

#define FIFO_LENGTH(F) (F.write_pos - F.read_pos)              /**< Macro to calculate length of a FIFO. */

/** @brief States for the app_uart state machine. */
typedef enum
{
    UART_OFF,                                                  /**< app_uart state OFF, indicating CTS is low. */
    UART_READY,                                                /**< app_uart state ON, indicating CTS is high. */
    UART_ON,                                                   /**< app_uart state TX, indicating UART is ongoing transmitting data. */
    UART_WAIT_CLOSE                                            /**< app_uart state WAIT CLOSE, indicating that CTS is low, but a byte is currently being transmitted on the line. */
} app_uart_states_t;

/** @brief State transition events for the app_uart state machine. */
typedef enum
{
    ON_CTS_HIGH,                                               /**< Event: CTS gone high. */
    ON_CTS_LOW,                                                /**< Event: CTS gone low. */
    ON_UART_PUT,                                               /**< Event: Application wants to transmit data. */
    ON_TX_READY,                                               /**< Event: Data has been transmitted on the uart and line is available. */
} app_uart_state_events_t;

static app_fifo_t                  m_rx_fifo;                  /**< RX FIFO buffer for storing data received on the UART until the application fetches them using app_uart_get(). */
static app_fifo_t                  m_tx_fifo;                  /**< TX FIFO buffer for storing data to be transmitted on the UART when TXD is ready. Data is put to the buffer on using app_uart_put(). */

static app_gpiote_user_id_t        m_gpiote_uid;               /**< GPIOTE user id for uart module. */
static uint32_t                    m_pin_cts_mask;             /**< CTS pin mask for uart module. */
static app_uart_event_handler_t    m_event_handler;            /**< Event handler function. */
static volatile app_uart_states_t  m_current_state = UART_OFF; /**< State of the state machine. */


/*@brief Action to disable the UART when entering the UART_OFF state.
 */
static void action_uart_deactivate(void)
{
    m_current_state         = UART_OFF;
    NRF_UART0->TASKS_STOPTX = 1;
    NRF_UART0->TASKS_STOPRX = 1;
    NRF_UART0->ENABLE       = (UART_ENABLE_ENABLE_Disabled << UART_ENABLE_ENABLE_Pos);
}


/*@brief Action to send next byte in the TX buffer. Called when (re-)entering the UART_ON state.
 *       If no more data is available in the TX buffer, the state machine will enter UART_READY state.
 */
static void action_tx_send()
{
    uint8_t byte;
    if (m_current_state != UART_ON)
    {
        // Start the UART.
        NRF_UART0->TASKS_STARTTX = 1;
    }

    // Get next byte from FIFO.
    if (app_fifo_get(&m_tx_fifo, &byte) == NRF_SUCCESS)
    {
        // Initiate transmission of byte.
        NRF_UART0->INTENCLR = (UART_INTENSET_TXDRDY_Set << UART_INTENSET_TXDRDY_Pos);
        NRF_UART0->TXD      = byte;
        m_current_state     = UART_ON;
        NRF_UART0->INTENSET = (UART_INTENSET_TXDRDY_Set << UART_INTENSET_TXDRDY_Pos);
    }
    else
    {
        // No more bytes in FIFO, terminate transmission.
        NRF_UART0->TASKS_STOPTX = 1;
        m_current_state         = UART_READY;
    }
}


/**@brief Handling of the ON_CTS_HIGH event.
 */
static void on_cts_high(void)
{
    switch (m_current_state)
    {
        case UART_READY:
            action_uart_deactivate();
            break;

        case UART_ON:
            m_current_state = UART_WAIT_CLOSE;
            break;

        default:
            // Nothing to do.
            break;
    }
}


/**@brief Handling of the ON_CTS_LOW event.
 */
static void on_cts_low(void)
{
    switch (m_current_state)
    {
        case UART_OFF:
            NRF_UART0->ENABLE        = (UART_ENABLE_ENABLE_Enabled << UART_ENABLE_ENABLE_Pos);
            NRF_UART0->TASKS_STARTRX = 1;

            if (FIFO_LENGTH(m_tx_fifo) != 0)
            {
                action_tx_send();
            }
            else
            {
                m_current_state = UART_READY;
            }
            break;

        case UART_WAIT_CLOSE:
            m_current_state = UART_ON;
            break;

        default:
            // Nothing to do.
            break;
    }
}


/**@brief Handling of the ON_TX_READY event.
 */
static void on_tx_ready(void)
{
    switch (m_current_state)
    {
        case UART_WAIT_CLOSE:
            action_uart_deactivate();
            break;

        case UART_ON:
        case UART_READY:
            action_tx_send();
            break;

        default:
            // Nothing to do.
            break;
    }
}


/**@brief Handling of the ON_UART_PUT event when application has put data in the TX buffer.
 */
static void on_uart_put(void)
{
    if (m_current_state == UART_READY)
    {
        action_tx_send();
    }
}


/**@brief State machine main event handler.
 *
 * @param[in]  event    Event that has occurred.
 */
static void on_uart_event(app_uart_state_events_t event)
{
    switch (event)
    {
        case ON_CTS_HIGH:
            on_cts_high();
            break;

        case ON_CTS_LOW:
            on_cts_low();
            break;

        case ON_TX_READY:
            on_tx_ready();
            break;

        case ON_UART_PUT:
            on_uart_put();
            break;

        default:
            // All valid events are handled above.
            break;
    }
}


/**@brief GPIOTE event handler.
 *
 * @param[in] event_pins_low_to_high   Mask telling which pin(s) generated an event from low->high.
 * @param[in] event_pins_high_to_low   Mask telling which pin(s) generated an event from high->low.
 */
static void gpiote_uart_event_handler(uint32_t event_pins_low_to_high,
                                      uint32_t event_pins_high_to_low)
{
    if ((event_pins_high_to_low & event_pins_low_to_high & m_pin_cts_mask) != 0)
    {
        // We have an indication from GPIOTE that the CTS pin has toggled high->low and low->high.
        // If this occurs, we must read the active pins in the GPIOTE module ourself.
        uint32_t active_pins;
        uint32_t err_code;

        err_code = app_gpiote_pins_state_get(m_gpiote_uid, &active_pins);
        if (err_code != NRF_SUCCESS)
        {
            // Pin reading was not possible, even though an event from GPIOTE was received that the
            // CTS pin toggled. If pin double toggled but status cannot be fetched we silently
            // return and keep the current UART status as-is.
            return;
        }
        event_pins_low_to_high &= active_pins;
        event_pins_high_to_low &= ~active_pins;
    }

    if ((event_pins_high_to_low & m_pin_cts_mask) != 0)
    {
        on_uart_event(ON_CTS_LOW);
    }
    else if ((event_pins_low_to_high & m_pin_cts_mask) != 0)
    {
        on_uart_event(ON_CTS_HIGH);
    }
    else
    {
        // Do nothing, as the CTS pin didn't toggle.
    }
}


/**@brief UART Interrupt handler.
 *
 * @details UART interrupt handler to process TX Ready when TXD is available, RX Ready when a byte
 *          is received, or in case of error when receiving a byte.
 */
void UART0_IRQHandler(void)
{
    // Handle reception
    if (NRF_UART0->EVENTS_RXDRDY != 0)
    {
        uint32_t err_code;
        
        // Clear UART RX event flag
        NRF_UART0->EVENTS_RXDRDY = 0;
        
        // Write received byte to FIFO
        err_code = app_fifo_put(&m_rx_fifo, (uint8_t)NRF_UART0->RXD);
        if (err_code != NRF_SUCCESS)
        {
            app_uart_evt_t app_uart_event;
            app_uart_event.evt_type          = APP_UART_NRF_ERROR;
            app_uart_event.data.error_source = err_code;
            m_event_handler(&app_uart_event);
        }
        // Notify that new data is available if this was first byte put in the buffer.
        else if (FIFO_LENGTH(m_rx_fifo) == 1)
        {
            app_uart_evt_t app_uart_event;
            app_uart_event.evt_type = APP_UART_DATA_READY;
            m_event_handler(&app_uart_event);
        }
        else
        {
            // Do nothing, only send event if first byte was added or overflow in FIFO occurred.
        }
    }
    
    // Handle transmission.
    if (NRF_UART0->EVENTS_TXDRDY != 0)
    {
        // Clear UART TX event flag.
        NRF_UART0->EVENTS_TXDRDY = 0;
        on_uart_event(ON_TX_READY);
    }
    
    // Handle errors.
    if (NRF_UART0->EVENTS_ERROR != 0)
    {
        uint32_t       error_source;
        app_uart_evt_t app_uart_event;

        // Clear UART ERROR event flag.
        NRF_UART0->EVENTS_ERROR = 0;
        
        // Clear error source.
        error_source        = NRF_UART0->ERRORSRC;
        NRF_UART0->ERRORSRC = error_source;

        app_uart_event.evt_type          = APP_UART_ERROR_SOURCE;
        app_uart_event.data.error_source = error_source;

        m_event_handler(&app_uart_event);
    }
}


/**@brief Initialization of UART when flow control is disabled.
 */
static void uart_no_flow_control_init(void)
{
    NRF_UART0->ENABLE        = (UART_ENABLE_ENABLE_Enabled << UART_ENABLE_ENABLE_Pos);
    NRF_UART0->EVENTS_RXDRDY = 0;
    NRF_UART0->EVENTS_TXDRDY = 0;

    NRF_UART0->TASKS_STARTTX = 1;
    NRF_UART0->TASKS_STARTRX = 1;
}


uint32_t app_uart_init(const app_uart_comm_params_t * p_comm_params,
                             app_uart_buffers_t *     p_buffers,
                             app_uart_event_handler_t event_handler,
                             app_irq_priority_t       irq_priority)
{
    uint32_t err_code;
    uint32_t gpiote_high_pins;
    uint32_t gpiote_pin_low_high_mask = 0;
    uint32_t gpiote_pin_high_low_mask = 0;

    m_current_state = UART_OFF;
    m_event_handler = event_handler;

    // Configure buffer RX buffer.
    err_code = app_fifo_init(&m_rx_fifo, p_buffers->rx_buf, p_buffers->rx_buf_size);
    if (err_code != NRF_SUCCESS)
    {
        // Propagate error code.
        return err_code;
    }

    // Configure buffer TX buffer.
    err_code = app_fifo_init(&m_tx_fifo, p_buffers->tx_buf, p_buffers->tx_buf_size);
    if (err_code != NRF_SUCCESS)
    {
        // Propagate error code.
        return err_code;
    }

    // Configure RX and TX pins.
    nrf_gpio_cfg_output(p_comm_params->tx_pin_no);
    nrf_gpio_cfg_input(p_comm_params->rx_pin_no, NRF_GPIO_PIN_NOPULL);

    NRF_UART0->PSELTXD = p_comm_params->tx_pin_no;
    NRF_UART0->PSELRXD = p_comm_params->rx_pin_no;

    // Configure baud rate and parity.
    NRF_UART0->BAUDRATE = (p_comm_params->baud_rate << UART_BAUDRATE_BAUDRATE_Pos);
    if (p_comm_params->use_parity)
    {
        NRF_UART0->CONFIG = (UART_CONFIG_PARITY_Included << UART_CONFIG_PARITY_Pos);
    }
    else
    {
        NRF_UART0->CONFIG = (UART_CONFIG_PARITY_Excluded << UART_CONFIG_PARITY_Pos);
    }

    if (p_comm_params->use_hardware_flow_control)
    {
        // Configure hardware flow control.
        nrf_gpio_cfg_output(p_comm_params->rts_pin_no);
        NRF_GPIO->OUT = 1 << p_comm_params->rts_pin_no;

        NRF_UART0->PSELCTS  = UART_PIN_DISCONNECTED;
        NRF_UART0->PSELRTS  = p_comm_params->rts_pin_no;
        NRF_UART0->CONFIG  |= (UART_CONFIG_HWFC_Enabled << UART_CONFIG_HWFC_Pos);

        // Setup the gpiote to handle pin events on cts-pin.
        // For the UART we want to detect both low->high and high->low transistions in order to
        // know when to activate/deactivate the TX/RX in the UART.
        // Configure pin.
        m_pin_cts_mask = (1 << p_comm_params->cts_pin_no);
        GPIO_PIN_CONFIG(p_comm_params->cts_pin_no,
                        GPIO_PIN_CNF_DIR_Input,
                        GPIO_PIN_CNF_INPUT_Connect,
                        GPIO_PIN_CNF_PULL_Disabled,
                        GPIO_PIN_CNF_DRIVE_S0S1,
                        GPIO_PIN_CNF_SENSE_Low);

        gpiote_pin_low_high_mask = (1 << p_comm_params->cts_pin_no);
        gpiote_pin_high_low_mask = (1 << p_comm_params->cts_pin_no);

        err_code = app_gpiote_user_register(&m_gpiote_uid,
                                            gpiote_pin_low_high_mask,
                                            gpiote_pin_high_low_mask,
                                            gpiote_uart_event_handler);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }

        err_code = app_gpiote_pins_state_get(m_gpiote_uid, &gpiote_high_pins);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }

        err_code = app_gpiote_user_enable(m_gpiote_uid);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }

        // UART CTS pin is active when low.
        if ((gpiote_high_pins & (1 << p_comm_params->cts_pin_no)) == 0)
        {
            on_uart_event(ON_CTS_LOW);
        }
        else
        {
            on_uart_event(ON_CTS_HIGH);
        }
    }
    else
    {
        uart_no_flow_control_init();
        m_current_state = UART_READY;
    }

    // Enable UART interrupt
    NRF_UART0->INTENCLR = 0xffffffffUL;
    NRF_UART0->INTENSET = (UART_INTENSET_RXDRDY_Set << UART_INTENSET_RXDRDY_Pos) |
                          (UART_INTENSET_TXDRDY_Set << UART_INTENSET_TXDRDY_Pos) |
                          (UART_INTENSET_ERROR_Set << UART_INTENSET_ERROR_Pos);

    NVIC_ClearPendingIRQ(UART0_IRQn);
    NVIC_SetPriority(UART0_IRQn, irq_priority);
    NVIC_EnableIRQ(UART0_IRQn);

    return NRF_SUCCESS;
}


uint32_t app_uart_get(uint8_t * p_byte)
{
    return app_fifo_get(&m_rx_fifo, p_byte);
}


uint32_t app_uart_put(uint8_t byte)
{
    uint32_t err_code = app_fifo_put(&m_tx_fifo, byte);

    on_uart_event(ON_UART_PUT);

    return err_code;
}


uint32_t app_uart_flush(void)
{
    uint32_t err_code;

    err_code = app_fifo_flush(&m_rx_fifo);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }

    err_code = app_fifo_flush(&m_tx_fifo);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }

    return NRF_SUCCESS;
}


uint32_t app_uart_get_connection_state(app_uart_connection_state_t * p_connection_state)
{
    *p_connection_state = m_current_state == UART_OFF ? APP_UART_DISCONNECTED : APP_UART_CONNECTED;

    return NRF_SUCCESS;
}

