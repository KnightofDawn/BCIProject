#include "spi_master.h"
#include "spi_master_config.h"
#include "nrf_delay.h"
#include "nrf.h"
#include "common.h"
#include "nrf_gpio.h"
#include "boards.h"
#include <stdbool.h>
#include <stdint.h>


static char tx_data[TX_RX_MSG_LENGTH]; /*!< SPI TX buffer */
static char rx_data[TX_RX_MSG_LENGTH]; /*!< SPI RX buffer */

#define DELAY_MS               1000       /*!< Timer Delay in milli-seconds */

// static bool test_spi_tx_rx(SPIModuleNumber mod_num, uint8_t lsb_first)
// {
//   unsigned char i;
//    
//    // Use SPI0, mode0 with lsb shifted as requested
//   uint32_t *spi_base_address = spi_master_init(mod_num, SPI_MODE0, (bool)lsb_first);
//   
// 
//   // Fill tx_data with some simple pattern, rx is filled with zero's so that after receiving from
//   // slave we verify rx_Data is same as tx_data
//   
//   for(i = 0; i < TX_RX_MSG_LENGTH; i++)
//   {
//     tx_data[i] = i;
//     rx_data[i] = 0;
//   }
// 
//   // Transmit TX_RX_MSG_LENGTH bytes from tx_data and receive same number of bytes and data into rx_data
//   if(!spi_master_tx_rx(spi_base_address, TX_RX_MSG_LENGTH, (const uint8_t *)tx_data, rx_data) )
//     return false;
// 
//   // Validate that we got all transmitted bytes back in the exact order
//   for(i = 0; i < TX_RX_MSG_LENGTH; i++)
//   {
//     if( tx_data[i] != rx_data[i] )
//       return false;
//   }
//   return true;
// }

int main(void)
{
  //Variable Declaration
  int i = 0;
  int num_byte_entered = 0;
  char temp_char = 0x00;
  simple_uart_config(RTS_PIN_NUMBER, TX_PIN_NUMBER, CTS_PIN_NUMBER, RX_PIN_NUMBER, HWFC);
  uint32_t *spi_base_address = spi_master_init(SPI0, SPI_MODE0, false);
  if (spi_base_address == 0) {
    return 0;
  }
  
  // setup GPIO
  nrf_gpio_cfg_output(LED0);
  nrf_gpio_cfg_output(LED1);
  nrf_gpio_cfg_input(DRDY_N_PIN, NRF_GPIO_PIN_PULLUP);
  
  
  while(true)
  {
     temp_char = 0x00;
     i = 0;
     while(temp_char != 0x0D) {
        temp_char = simple_uart_get();
        tx_data[i] = temp_char;
        i++;        
     }

     num_byte_entered = i-1;
     for (int j = 0; j<num_byte_entered; j++) {
        simple_uart_put(tx_data[j]);
     }
     
     //spend OPCODE
     spi_master_tx_rx(spi_base_address, num_byte_entered, (const uint8_t *)tx_data, rx_data);
     
     // READ REGISTER DATA
     // if (spi_master_rx(spi_base_address, 1, rx_data)) {
     //     nrf_gpio_pin_write(LED0, 0);
     //     nrf_delay_ms(DELAY_MS);
     //     nrf_gpio_pin_write(LED0, 1);
     // }
     // else {
     //    nrf_gpio_pin_write(LED1, 0);
     //    nrf_delay_ms(DELAY_MS);
     //    nrf_gpio_pin_write(LED1, 1);
     // }
     // while(nrf_gpio_pin_read(DRDY_N_PIN) == 0) {
     //     data_rdy = nrf_gpio_pin_read(DRDY_N_PIN);
     // }
     
     for (int j = 0; j<num_byte_entered; j++) {
        simple_uart_put(rx_data[j]);
     }
  }
}