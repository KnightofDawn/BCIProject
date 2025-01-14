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
#define WAKEUP			0
#define STANDBY		1
#define RESET				2
#define START				3
#define STOP				4

#define RDATAC			5	
#define SDATAC			6
#define RDATA				7

#define RREG				8
#define WREG				9

int main(void)
{
  //Variable Declaration
  int i = 0;
  int num_byte_entered = 0;
  char temp_char = 0x00;
  bool data_rdy = 1;
	
	simple_uart_config(RTS_PIN_NUMBER, TX_PIN_NUMBER, CTS_PIN_NUMBER, RX_PIN_NUMBER, HWFC);
  uint32_t *spi_base_address = spi_master_init(SPI0, SPI_MODE1, false);
  if (spi_base_address == 0) {
    return 0;
  }
  
  // setup GPIO
  nrf_gpio_cfg_output(LED0);
  nrf_gpio_cfg_output(LED1);
  nrf_gpio_cfg_input(DRDY_N_PIN, NRF_GPIO_PIN_PULLUP);
  
  int numberofregister = 0;
  int command				=	 0;
  bool rdatac					= true;
  bool standby					= false;
  bool conversionstarted = false;
  while(true)
  {
		memset(tx_data,0,TX_RX_MSG_LENGTH);
		memset(rx_data,0,TX_RX_MSG_LENGTH);
		temp_char = 0x00;
		temp_char = simple_uart_get();
		numberofregister = 0;
		switch(temp_char)
		{
		case 0x02:
			command = WAKEUP;
			break;
		case 0x04:
			command = STANDBY;
			break;
		case 0x06:
			command = RESET;
			break;
		case 0x08:
			command = START;
			break;
		case 0x0A:
			command = STOP;
			break;
		case 0x10:
			command = RDATAC;
			break;
		case 0x11:
			command = SDATAC;
			break;
		case 0x12:
			command = RDATA;
			break;
		default:
			if(temp_char & 0x20)
			{
				command = RREG;
				//numberofregister  = temp_char & 0x31;
			}
			else if(temp_char & 0x40)
			{
				command = WREG;
				//numberofregister =  temp_char & 0x63;
			}
			else
				command = 0;
			break;
		}

		switch(command)
		{
			////////////////////
		case WAKEUP:
			tx_data[0] = temp_char;
/*	
		for(int i = 0; i < 4; ++i)
				{
					temp_char = simple_uart_get();
					tx_data[i+1] = temp_char;
				}
		*/
			//spi_master_tx(spi_base_address, 1, (const uint8_t *)tx_data);
			spi_master_tx_rx(spi_base_address, 4, (const uint8_t *)tx_data, rx_data);
			standby = false;
			break;
		case STANDBY:
			standby = true;
		case RESET:
		case START:
		case STOP:
			tx_data[0] = temp_char;
/*		
		for(int i = 0; i < 4; ++i)
			{
				temp_char = simple_uart_get();
				tx_data[i+1] = temp_char;
			}
		*/
		//spi_master_tx(spi_base_address, 1, (const uint8_t *)tx_data);
			spi_master_tx_rx(spi_base_address, 4, (const uint8_t *)tx_data, rx_data);
		
			if(standby)
				break;
			if(command == RESET)
			{
					numberofregister = 0;
					command				=	 0;
					rdatac					= true;
					standby					= false;
					conversionstarted = false;
					memset(tx_data,0,TX_RX_MSG_LENGTH);
					memset(rx_data,0,TX_RX_MSG_LENGTH);
			}
			
			if(command == START)
				conversionstarted = true;
			else if(command == STOP)
				conversionstarted = false;

			
			break;
			///////////////////////////////
		case RDATAC:
			tx_data[0] = temp_char;
/*
		for(int i = 0; i < 4; ++i)
			{
				temp_char = simple_uart_get();
				tx_data[i+1] = temp_char;
			}
		*/
			if(!rdatac)
			{
				//spi_master_tx(spi_base_address, 1, (const uint8_t *)tx_data);
				spi_master_tx_rx(spi_base_address, 4, (const uint8_t *)tx_data, rx_data);
				rdatac = true;
			}
			break;
		case SDATAC:
			tx_data[0] = temp_char;
/*	
		for(int i = 0; i < 4; ++i)
			{
					temp_char = simple_uart_get();
					tx_data[i+1] = temp_char;
			}
*/
			//if(rdatac)
			{
				//spi_master_tx(spi_base_address, 1, (const uint8_t *)tx_data);
				spi_master_tx_rx(spi_base_address, 4, (const uint8_t *)tx_data, rx_data);
				rdatac = false;
			}
			break;
		case RDATA:
			tx_data[0] = temp_char;
/*
		for(int i = 0; i < 4; ++i)
		{
				temp_char = simple_uart_get();
			tx_data[i+1] = temp_char;
		}
		*/
			if(conversionstarted && !rdatac)
			{
				int count = 200;
				data_rdy = nrf_gpio_pin_read(DRDY_N_PIN);
				while(data_rdy && count >= 0) 
				{
					data_rdy = nrf_gpio_pin_read(DRDY_N_PIN);
					count--;
				}	
				if(count > 0)
				{
					//spi_master_tx(spi_base_address, 1, (const uint8_t *)tx_data);
					//spi_master_tx_rx(spi_base_address, 1, (const uint8_t *)tx_data, rx_data);
					spi_master_tx_rx(spi_base_address, 27, (const uint8_t *)tx_data, rx_data);

					for (int j = 0; j<27; j++) 
					{
						simple_uart_put(rx_data[j]);
					}
				}
			}
			break;
			///////////////////////////
		case RREG:
			tx_data[0]				= temp_char;
			temp_char				  = simple_uart_get();
			tx_data[1]				= temp_char;
			numberofregister	= temp_char;
			/*
		  for(int i = 0; i < 3; ++i)
			{
				temp_char = simple_uart_get();
				 tx_data[i + 2] = temp_char;
			}
*/
			//TEST
			//for(int j = 0; j < 4; ++j)
			//	simple_uart_put(tx_data[j]);
			//
			spi_master_tx_rx(spi_base_address, 4, (const uint8_t *)tx_data, rx_data);
			break;
		case WREG:
			tx_data[0]				= temp_char;
			temp_char				= simple_uart_get();
			tx_data[1]				= temp_char;
			numberofregister	= temp_char + 1;
			for(int i = 0; i < numberofregister; ++i)
				tx_data[i+2] = simple_uart_get();	  
		/*		
			for(int i = 2; i < 5; ++i)
			{
				temp_char = simple_uart_get();
				 tx_data[i] = temp_char;
			}
		*/
			spi_master_tx_rx(spi_base_address, 4, (const uint8_t *)tx_data, rx_data);
			break;

		default:
			break;
		}

		if(conversionstarted && rdatac)
		{
			int count = 200;
			data_rdy = nrf_gpio_pin_read(DRDY_N_PIN);
			while(data_rdy && count >= 0) 
			{
				data_rdy = nrf_gpio_pin_read(DRDY_N_PIN);
				count--;
			}	
			if(count > 0)
			{
				spi_master_tx_rx(spi_base_address, 27, (const uint8_t *)tx_data, rx_data);

				for (int j = 0; j<27; j++) 
				{
					simple_uart_put(rx_data[j]);
				}
			}
		}
		
		else if(command == RREG)
		{
		for(int j = 0; j < 4; ++j)
				simple_uart_put(tx_data[j]);
		for(int j = 0; j < 4; ++j)
				simple_uart_put(rx_data[j]);

		}
		/*
		for (int k = 0; k<32; k++) 
		{
		temp_char = 0x00;
		i = 0;
		while(temp_char != 0x0D) 
		{
			  temp_char = simple_uart_get();
			  tx_data[i] = temp_char;
			  i++;        
		  }

		  num_byte_entered = i-1;
		  for (int j = 0; j<num_byte_entered; j++) 
		  {
			  simple_uart_put(tx_data[j]);
		  }

		  //spend OPCODE
		  spi_master_tx_rx(spi_base_address, num_byte_entered, (const uint8_t *)tx_data, rx_data);

		  for (int j = 0; j<num_byte_entered; j++) 
		  {
			  simple_uart_put(rx_data[j]);
		  }
	  }

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
	  while(true)
	  { 
		  while(nrf_gpio_pin_read(DRDY_N_PIN) == 1) 
		  {
			  data_rdy = nrf_gpio_pin_read(DRDY_N_PIN);
		  }	

		  spi_master_tx_rx(spi_base_address, 216, (const uint8_t *)tx_data, rx_data);

		  for (int j = 0; j<216; j++) 
		  {
			  simple_uart_put(rx_data[j]);
		  }
	  }
	  */
  }
}