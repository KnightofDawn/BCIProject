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

#include "ble_bondmngr.h"
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "nordic_common.h"
#include "nrf_error.h"
#include "ble_gap.h"
#include "ble_srv_common.h"
#include "app_util.h"
#include "nrf_assert.h"
#include "nrf.h"
#include "nrf51_bitfields.h"
#include "ble_flash.h"
#include "ble_bondmngr_cfg.h"


#define CCCD_SIZE                  6                                                           /**< Number of bytes needed for storing the state of one CCCD. */
#define CRC_SIZE                   2                                                           /**< Size of CRC in sys_attribute data. */
#define SYS_ATTR_BUFFER_MAX_LEN    (((BLE_BONDMNGR_CCCD_COUNT + 1) * CCCD_SIZE) + CRC_SIZE)    /**< Size of sys_attribute data. */
#define MAX_NUM_MASTER_WHITE_LIST  MIN(BLE_BONDMNGR_MAX_BONDED_MASTERS, 8)

#define MAX_BONDS_IN_FLASH  (BLE_FLASH_PAGE_SIZE / (sizeof(master_bond_t) + sizeof(uint32_t))) /**< Maximum number of bonds that can fit into one flash page. */

/**@brief Structure for holding bonding information for one master.
 */
typedef struct
{
    int32_t                        master_handle;                         /**< Master's handle (NOTE: Size is 32 bits just to make struct size dividable by 4). */
    ble_gap_evt_auth_status_t      auth_status;                           /**< Master authentication data. */
    ble_gap_evt_sec_info_request_t master_id_info;                        /**< Master identification info. */
    ble_gap_addr_t                 master_addr;                           /**< Master's address. */
} master_bond_t;

STATIC_ASSERT(sizeof(master_bond_t) % 4 == 0);

/**@brief Structure for holding system attribute information for one master.
 */
typedef struct
{
    int32_t  master_handle;                                               /**< Master's handle (NOTE: Size is 32 bits just to make struct size dividable by 4). */
    uint8_t  sys_attr[SYS_ATTR_BUFFER_MAX_LEN];                           /**< Master sys_attribute data. */
    uint32_t sys_attr_size;                                               /**< Master sys_attribute data's size (NOTE: Size is 32 bits just to make struct size dividable by 4). */
} master_sys_attr_t;

STATIC_ASSERT(sizeof(master_sys_attr_t) % 4 == 0);

/**@brief Structure for holding data for one master.
 */
typedef struct
{
    master_bond_t     bond;                                               /**< Bonding information. */
    master_sys_attr_t sys_attr;                                           /**< System attribute information. */
} master_t;

/**@brief Structure for holding whitelist address data.
 */
typedef struct
{
    int8_t           master_handle;                                       /**< Master's handle. */
    ble_gap_addr_t * p_addr;                                              /**< Pointer to the master's address if BLE_GAP_ADDR_TYPE_PUBLIC. */
} whitelist_addr_t;

/**@brief Structure for holding whitelist IRK data.
 */
typedef struct
{
    int8_t           master_handle;                                       /**< Master's handle. */
    ble_gap_irk_t  * p_irk;                                               /**< Pointer to the master's irk if available. */
} whitelist_irk_t;

static bool                m_is_bondmngr_initialized = false;             /**< Flag for checking if module has been initialized. */
static ble_bondmngr_init_t m_bondmngr_config;                             /**< Configuration as specified by the application. */
static uint16_t            m_conn_handle;                                 /**< Current connection handle. */
static master_t            m_master;                                      /**< Current master data. */
static master_t            m_masters_db[BLE_BONDMNGR_MAX_BONDED_MASTERS]; /**< Pointer to start of bonded masters database. */
static uint8_t             m_masters_in_db_count;                         /**< Number of bonded masters. */
static whitelist_addr_t    m_whitelist_addr[MAX_NUM_MASTER_WHITE_LIST];   /**< List of master's addresses  for the white list. */
static whitelist_irk_t     m_whitelist_irk[MAX_NUM_MASTER_WHITE_LIST];    /**< List of master's irks  for the white list. */
static uint8_t             m_addr_count;                                  /**< Number of addresses in the white list. */
static uint8_t             m_irk_count;                                   /**< Number of irks in the white list. */
static uint16_t            m_crc_bond_info;                               /**< Combined CRC for all bonding information currently stored in flash. */
static uint16_t            m_crc_sys_attr;                                /**< Combined CRC for all system attributes currently stored in flash. */
static uint32_t *          mp_flash_bond_info;                            /**< Pointer to flash location to write next bonding information. */
static uint32_t *          mp_flash_sys_attr;                             /**< Pointer to flash location to write next System Attribute information. */
static uint8_t             m_bond_info_in_flash_count;                    /**< Number of bonding information currently stored in flash. */
static uint8_t             m_sys_attr_in_flash_count;                     /**< Number of System Attributes ccurrently stored in flash. */
 

/**@brief Extract CRC from flash header word.
 *
 * @param[in]  header   Header containing CRC and magic number.
 * @param[out] p_crc    Extracted CRC.
 *
 * @retval      NRF_SUCCESS              CRC successfully extracted.
 * @retval      NRF_ERROR_NOT_FOUND      Flash seems to be empty.
 * @retval      NRF_ERROR_INVALID_DATA   Header does not contain the magic number.
 */
static uint32_t crc_extract(uint32_t header, uint16_t * p_crc)
{
    if ((header & 0xFFFF0000U) == BLE_FLASH_MAGIC_NUMBER)
    {
        *p_crc = (uint16_t)(header & 0x0000FFFFU);
        
        return NRF_SUCCESS;
    }
    else if (header == 0xFFFFFFFFU)
    {
        return NRF_ERROR_NOT_FOUND;
    }
    else
    {
        return NRF_ERROR_INVALID_DATA;
    }
}


/**@brief Store bonding info for specified master to flash.
 *
 * @param[in]  p_bond   Bonding information to be stored.
 *
 * @return     NRF_SUCCESS on success, an error_code otherwise.
 */
static uint32_t bond_info_store(master_bond_t * p_bond)
{
    uint32_t err_code;

    // Check if flash is full
    if (m_bond_info_in_flash_count >= MAX_BONDS_IN_FLASH)
    {
        return NRF_ERROR_NO_MEM;
    }

    // Check if this is the first bond to be stored
    if (m_bond_info_in_flash_count == 0)
    {
        // Initialize CRC
        m_crc_bond_info = ble_flash_crc16_compute(NULL, 0, NULL);
    
        // Find pointer to start of bond information flash block
        err_code = ble_flash_page_addr(m_bondmngr_config.flash_page_num_bond, &mp_flash_bond_info);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
    }
    
    // Write bonding information
    err_code = ble_flash_block_write(mp_flash_bond_info + 1,
                                     (uint32_t *)p_bond,
                                     sizeof(master_bond_t) / sizeof(uint32_t));
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    m_crc_bond_info = ble_flash_crc16_compute((uint8_t *)p_bond, 
                                              sizeof(master_bond_t), 
                                              &m_crc_bond_info);
    
    // Write header
    err_code = ble_flash_word_write(mp_flash_bond_info, BLE_FLASH_MAGIC_NUMBER | m_crc_bond_info);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    
    // Update flash pointer
    mp_flash_bond_info += (sizeof(master_bond_t) / sizeof(uint32_t)) + 1;
    
    m_bond_info_in_flash_count++;
    return NRF_SUCCESS;
}


/**@brief Store system attribute info of specified master to flash.
 *
 * @param[in]  p_sys_attr   System attribute to be stored.
 *
 * @return     NRF_SUCCESS on success, an error_code otherwise.
 */
static uint32_t sys_attr_store(master_sys_attr_t * p_sys_attr)
{
    uint32_t err_code;

    // Check if flash is full
    if (m_sys_attr_in_flash_count >= MAX_BONDS_IN_FLASH)
    {
        return NRF_ERROR_NO_MEM;
    }

    // Check if this is the first syste attribute to be stored
    if (m_sys_attr_in_flash_count == 0)
    {
        // Initialize CRC
        m_crc_sys_attr = ble_flash_crc16_compute(NULL, 0, NULL);
    
        // Find pointer to start of system attribute flash block
        err_code = ble_flash_page_addr(m_bondmngr_config.flash_page_num_sys_attr, 
                                       &mp_flash_sys_attr);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
    }
    
    // Write system attribute information in flash
    err_code = ble_flash_block_write(mp_flash_sys_attr + 1,
                                    (uint32_t *)p_sys_attr,
                                    sizeof(master_sys_attr_t) / sizeof(uint32_t));
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    m_crc_sys_attr = ble_flash_crc16_compute((uint8_t *)p_sys_attr, 
                                             sizeof(master_sys_attr_t), 
                                             &m_crc_sys_attr);
    
    // Write header
    err_code = ble_flash_word_write(mp_flash_sys_attr, BLE_FLASH_MAGIC_NUMBER | m_crc_sys_attr);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    
    // Update flash pointer
    mp_flash_sys_attr += ((sizeof(master_sys_attr_t) / sizeof(uint32_t)) + 1);
    
    m_sys_attr_in_flash_count++;
    return NRF_SUCCESS;
}


/**@brief Load bonding information for one master from flash.
 *
 * @param[out] p_bond   Loaded bonding information.
 *
 * @return     NRF_SUCCESS on success, otherwise an error code.
 */
static uint32_t bonding_info_load_from_flash(master_bond_t * p_bond)
{
    uint32_t err_code;
    uint16_t crc_header;

    // Check if this is the first bond to be loaded, in which case the 
    // m_bond_info_in_flash_count variable would have the intial value 0.
    if (m_bond_info_in_flash_count == 0)
    {
        // Initialize CRC
        m_crc_bond_info = ble_flash_crc16_compute(NULL, 0, NULL);
    
        // Find pointer to start of bond information flash block
        err_code = ble_flash_page_addr(m_bondmngr_config.flash_page_num_bond, &mp_flash_bond_info);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
    }
    
    // Extract CRC from header
    err_code = crc_extract(*mp_flash_bond_info, &crc_header);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    
    // Load master
    *p_bond = *(master_bond_t *)(mp_flash_bond_info + 1);
    
    // Check CRC
    m_crc_bond_info = ble_flash_crc16_compute((uint8_t *)p_bond, 
                                              sizeof(master_bond_t), 
                                              &m_crc_bond_info);
    if (m_crc_bond_info == crc_header)
    {
        m_bond_info_in_flash_count++;
        mp_flash_bond_info += (sizeof(master_bond_t) / sizeof(uint32_t)) + 1;
        
        return NRF_SUCCESS;
    }
    else
    {
        return NRF_ERROR_INVALID_DATA;
    }
}



/**@brief Load system attribute information for one master from flash.
 *
 * @param[out] p_sys_attr   Loaded system attribute information.
 *
 * @return     NRF_SUCCESS on success, otherwise an error code.
 */
static uint32_t sys_attr_load_from_flash(master_sys_attr_t * p_sys_attr)
{
    uint32_t err_code;
    uint16_t crc_header;

    // Check if this is the first system attribute to be loaded, in which case the 
    // m_sys_attr_in_flash_count variable would have the intial value 0.
    if (m_sys_attr_in_flash_count == 0)
    {
        // Initialize CRC
        m_crc_sys_attr = ble_flash_crc16_compute(NULL, 0, NULL);
    
        // Find pointer to start of system attribute flash block
        err_code = ble_flash_page_addr(m_bondmngr_config.flash_page_num_sys_attr, 
                                       &mp_flash_sys_attr);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
    }
    
    // Extract CRC from header
    err_code = crc_extract(*mp_flash_sys_attr, &crc_header);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    
    // Read system attribute from flash
    *p_sys_attr = *(master_sys_attr_t *)(mp_flash_sys_attr + 1);
    
    // Check CRC
    m_crc_sys_attr = ble_flash_crc16_compute((uint8_t *)p_sys_attr, 
                                             sizeof(master_sys_attr_t), 
                                             &m_crc_sys_attr);
    if (m_crc_sys_attr == crc_header)
    {
        m_sys_attr_in_flash_count++;
        mp_flash_sys_attr += (sizeof(master_sys_attr_t) / sizeof(uint32_t)) + 1;
        
        return NRF_SUCCESS;
    }
    else
    {
        return NRF_ERROR_INVALID_DATA;
    }
}


/**@brief Erase flash pages for both bonding information and system attribute information.
 *
 * @return     NRF_SUCCESS on success, otherwise an error code.
 */
static uint32_t flash_pages_erase(void)
{
    uint32_t err_code;
    
    err_code = ble_flash_page_erase(m_bondmngr_config.flash_page_num_bond);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }

    err_code = ble_flash_page_erase(m_bondmngr_config.flash_page_num_sys_attr);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    
    return NRF_SUCCESS;
}


/**@brief Check if bonding information in memory is different from the one in flash.
 *
 * @return     TRUE if bonding information has changed, FALSE otherwise.
 */
static bool bond_info_changed(void)
{
    int      i;
    uint16_t crc = ble_flash_crc16_compute(NULL, 0, NULL);
    
    // Compute CRC for all bonds in database
    for (i = 0; i < m_masters_in_db_count; i++)
    {
        crc = ble_flash_crc16_compute((uint8_t *)&m_masters_db[i].bond,
                                      sizeof(master_bond_t),
                                      &crc);
    }
    
    // Compare to CRC of bonds in flash
    return (crc != m_crc_bond_info);
}


/**@brief Check if system attribute information in memory is different from the one in flash.
 *
 * @return     TRUE if system attribute information has changed, FALSE otherwise.
 */
static bool sys_attr_changed(void)
{
    int      i;
    uint16_t crc = ble_flash_crc16_compute(NULL, 0, NULL);
    
    // Compute CRC for all system attributes in database
    for (i = 0; i < m_masters_in_db_count; i++)
    {
        crc = ble_flash_crc16_compute((uint8_t *)&m_masters_db[i].sys_attr,
                                      sizeof(master_sys_attr_t),
                                      &crc);
    }
    
    // Compare to CRC of system attributes in flash with that of the system attributes in memory.
    return (crc != m_crc_sys_attr);
}


/**@brief Set system attributes for specified master, or clear system attributes if master has no
 *        system attributes.
 *
 * @param[in]  p_master   Master for which the system attributes is to be set.
 *
 * @return     NRF_SUCCESS on success, otherwise an error code.
 */
static uint32_t master_sys_attr_set(master_t * p_master)
{
    uint8_t * p_sys_attr;
    
    if (m_master.sys_attr.sys_attr_size != 0)
    {
        p_sys_attr = m_master.sys_attr.sys_attr;
    }
    else
    {
        p_sys_attr = NULL;
    }
    
    return sd_ble_gatts_sys_attr_set(m_conn_handle, p_sys_attr, m_master.sys_attr.sys_attr_size);
}


/**@brief Update white list data structures.
 */
static void update_white_list(void)
{
    int i;
    
    for (i = 0, m_addr_count = 0, m_irk_count = 0; i < m_masters_in_db_count; i++)
    {
        master_bond_t * p_bond = &m_masters_db[i].bond;
        
        if (p_bond->auth_status.central_kex.irk)
        {
            m_whitelist_irk[m_irk_count].master_handle = p_bond->master_handle;
            m_whitelist_irk[m_irk_count].p_irk         = &(p_bond->auth_status.central_keys.irk);

            m_irk_count++;
        }
        else
        {
            m_whitelist_addr[m_addr_count].master_handle = p_bond->master_handle;
            m_whitelist_addr[m_addr_count].p_addr        = &(p_bond->master_addr);
                
            m_addr_count++;
        }
    }
}


/**@brief Event handler for authentication status message from new master.
 *
 * @details This function adds the new master to database. It also stores the master's bonding
 *          information to flash, and notifies the application that a new bond has been created and
 *          also prepares the stack for connection with this new master by setting the system
 *          attributes.
 *
 * @param[in]  p_auth_status   New authentication status.
 *
 * @return     NRF_SUCCESS on success, otherwise an error code.
 */
static uint32_t on_auth_status_from_new_master(ble_gap_evt_auth_status_t * p_auth_status)
{
    uint32_t err_code;
    
    if (m_masters_in_db_count >= BLE_BONDMNGR_MAX_BONDED_MASTERS)
    {
        return NRF_ERROR_NO_MEM;
    }

    // Update master
    m_master.bond.auth_status        = *p_auth_status;
    m_master.bond.master_id_info.div = p_auth_status->periph_keys.enc_info.div;
    m_master.sys_attr.sys_attr_size  = 0;

    // Add new master to database
    m_master.bond.master_handle           = m_masters_in_db_count;
    m_masters_db[m_masters_in_db_count++] = m_master;
    
    update_white_list();

    // Clear system attribute info
    err_code = sd_ble_gatts_sys_attr_set(m_conn_handle, NULL, 0);
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    
    // Write new master's bonding information to flash
    err_code = bond_info_store(&m_master.bond);
    if ((err_code == NRF_ERROR_NO_MEM) && (m_bondmngr_config.evt_handler != NULL))
    {
        ble_bondmngr_evt_t evt;
        
        evt.evt_type      = BLE_BONDMNGR_EVT_BOND_FLASH_FULL;
        evt.master_handle = m_master.bond.master_handle;
        
        m_bondmngr_config.evt_handler(&evt);
    }
    else if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }
    
    // Pass event to application
    if (m_bondmngr_config.evt_handler != NULL)
    {
        ble_bondmngr_evt_t evt;
        
        evt.evt_type      = BLE_BONDMNGR_EVT_NEW_BOND;
        evt.master_handle = m_master.bond.master_handle;
        
        m_bondmngr_config.evt_handler(&evt);
    }
    
    return NRF_SUCCESS;
}


/**@brief Update the current master's entry in the database.
 */
static uint32_t master_update(void)
{
    uint32_t err_code;
    int32_t  master_handle = m_master.bond.master_handle;
    
    if ((master_handle >= 0) && (master_handle < m_masters_in_db_count))
    {
        m_masters_db[master_handle] = m_master;
        update_white_list();

        err_code = NRF_SUCCESS;
    }
    else
    {
        err_code = NRF_ERROR_INVALID_PARAM;
    }

    return err_code;
}


/**@brief Find master corresponding to the specified diversificator.
 *
 * @param[in]  master_div   Diversificator to search for.
 * @return     NRF_SUCCESS on success, otherwise an error code.
 */
static uint32_t master_find_in_db(uint16_t master_div)
{
    int i;
    
    m_master.bond.master_handle = INVALID_MASTER_HANDLE;
    for (i = 0; i < m_masters_in_db_count; i++)
    {
        if (master_div == m_masters_db[i].bond.master_id_info.div)
        {
            m_master = m_masters_db[i];
            return NRF_SUCCESS;
        }
    }
    
    return NRF_ERROR_NOT_FOUND;
}


/**@brief Load bonding information and system attribute information from flash.
 *
 * @return     NRF_SUCCESS on success, otherwise an error code.
 */
static uint32_t load_all_from_flash(void)
{
    uint32_t err_code;
    int      i;
    
    // Load bond information for all masters
    m_masters_in_db_count = 0;

    while (m_masters_in_db_count < BLE_BONDMNGR_MAX_BONDED_MASTERS)
    {
        master_bond_t master_bond_info;
        int           master_handle;
        
        // Load bonding information
        err_code = bonding_info_load_from_flash(&master_bond_info);
        if (err_code == NRF_ERROR_NOT_FOUND)
        {
            // No more bonds in flash
            break;
        }
        else if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
        
        master_handle = master_bond_info.master_handle;
        if (master_handle > m_masters_in_db_count)
        {
            // Master handle value(s) missing in flash. This should never happen.
            return NRF_ERROR_INVALID_DATA;
        }
        else
        {
            // Add/update bonding information in master array
            m_masters_db[master_handle].bond = master_bond_info;
            if (master_handle == m_masters_in_db_count)
            {
                // New master handle, clear system attribute information
                m_masters_db[master_handle].sys_attr.sys_attr_size = 0;
                m_masters_db[master_handle].sys_attr.master_handle = INVALID_MASTER_HANDLE;
                m_masters_in_db_count++;
            }
            else
            {
                // Entry was updated, do nothing
            }
        }
    }

    // Load system attribute information for all previously known masters.
    for (i = 0; i < m_masters_in_db_count; i++)
    {
        master_sys_attr_t master_sys_attr;
        
        // Load system attribute information
        err_code = sys_attr_load_from_flash(&master_sys_attr);
        if (err_code == NRF_ERROR_NOT_FOUND)
        {
            // No more system attributes in flash
            break;
        }
        else if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
        
        if (master_sys_attr.master_handle > m_masters_in_db_count)
        {
            // Master handle value(s) missing in flash. This should never happen.
            return NRF_ERROR_INVALID_DATA;
        }
        else
        {
            // Add/update bonding information in master array
            m_masters_db[master_sys_attr.master_handle].sys_attr = master_sys_attr;
        }
    }
    
    // Initialize the remaining empty bond entries in the memory.
    for (i = m_masters_in_db_count; i < BLE_BONDMNGR_MAX_BONDED_MASTERS; i++)
    {
        m_masters_db[i].bond.master_handle     = INVALID_MASTER_HANDLE;
        m_masters_db[i].sys_attr.sys_attr_size = 0;
        m_masters_db[i].sys_attr.master_handle = INVALID_MASTER_HANDLE;
    }
    
    // Update write list data structures
    update_white_list();
    
    return NRF_SUCCESS;
}


/**@brief Check if two ble_gap_sec_levels_t variables are equal.
 *
 * @param[in]  p_sec_levels_1   Variable 1.
 * @param[in]  p_sec_levels_2   Variable 2.
 *
 * @return     TRUE if all fields in the two variables are equal, FALSE otherwise.
 */
static bool sec_levels_equal(ble_gap_sec_levels_t * p_sec_levels_1,
                             ble_gap_sec_levels_t * p_sec_levels_2)
{
    return ((p_sec_levels_1->lv1 == p_sec_levels_2->lv1) &&
            (p_sec_levels_1->lv2 == p_sec_levels_2->lv2) &&
            (p_sec_levels_1->lv3 == p_sec_levels_2->lv3));
}


/**@brief Check if two ble_gap_sec_keys_t variables are equal.
 *
 * @param[in]  p_sec_keys_1   Variable 1.
 * @param[in]  p_sec_keys_2   Variable 2.
 *
 * @return     TRUE if all fields in the two variables are equal, FALSE otherwise.
 */
static bool sec_keys_equal(ble_gap_sec_keys_t * p_sec_keys_1,
                           ble_gap_sec_keys_t * p_sec_keys_2)
{
    return ((p_sec_keys_1->ltk       == p_sec_keys_2->ltk)       &&
            (p_sec_keys_1->ediv_rand == p_sec_keys_2->ediv_rand) &&
            (p_sec_keys_1->irk       == p_sec_keys_2->irk)       &&
            (p_sec_keys_1->address   == p_sec_keys_2->address)   &&
            (p_sec_keys_1->csrk      == p_sec_keys_2->csrk));
}


/**@brief Check if two ble_gap_enc_info_t variables are equal.
 *
 * @param[in]  p_enc_info_1   Variable 1.
 * @param[in]  p_enc_info_2   Variable 2.
 *
 * @return     TRUE if all fields in the two variables are equal, FALSE otherwise.
 */
static bool enc_info_equal(ble_gap_enc_info_t * p_enc_info_1,
                           ble_gap_enc_info_t * p_enc_info_2)
{
    return ((p_enc_info_1->div     == p_enc_info_2->div)     &&
            (p_enc_info_1->auth    == p_enc_info_2->auth)    &&
            (p_enc_info_1->ltk_len == p_enc_info_2->ltk_len) &&
            (memcmp(p_enc_info_1->ltk, p_enc_info_2->ltk, p_enc_info_1->ltk_len) == 0));
}


/**@brief Check if two ble_gap_irk_t variables are equal.
 *
 * @param[in]  p_irk_1   Variable 1.
 * @param[in]  p_irk_2   Variable 2.
 *
 * @return     TRUE if all fields in the two variables are equal, FALSE otherwise.
 */
static bool irk_equal(ble_gap_irk_t * p_irk_1,
                      ble_gap_irk_t * p_irk_2)
{
    return (memcmp(p_irk_1->irk, p_irk_2->irk, BLE_GAP_SEC_KEY_LEN) == 0);
}


/**@brief Check if two ble_gap_addr_t variables are equal.
 *
 * @param[in]  p_addr_1   Variable 1.
 * @param[in]  p_addr_2   Variable 2.
 *
 * @return     TRUE if all fields in the two variables are equal, FALSE otherwise.
 */
static bool addr_equal(ble_gap_addr_t * p_addr_1,
                       ble_gap_addr_t * p_addr_2)
{
    return ((p_addr_1->addr_type == p_addr_2->addr_type) &&
            (memcmp(p_addr_1->addr, p_addr_2->addr, BLE_GAP_ADDR_LEN) == 0));
}


/**@brief Check if two ble_gap_evt_auth_status_t variables are equal.
 *
 * @param[in]  p_auth_status_1   Variable 1.
 * @param[in]  p_auth_status_2   Variable 2.
 *
 * @return     TRUE if all fields in the two variables are equal, FALSE otherwise.
 */
static bool auth_status_equal(ble_gap_evt_auth_status_t * p_auth_status_1,
                              ble_gap_evt_auth_status_t * p_auth_status_2)
{
    return ((p_auth_status_1->auth_status == p_auth_status_2->auth_status)                    &&
            (p_auth_status_1->error_src   == p_auth_status_2->error_src)                      &&
            sec_levels_equal(&p_auth_status_1->sm1_levels, &p_auth_status_2->sm1_levels)      &&
            sec_levels_equal(&p_auth_status_1->sm2_levels, &p_auth_status_2->sm2_levels)      &&
            sec_keys_equal(&p_auth_status_1->periph_kex, &p_auth_status_2->periph_kex)        &&
            sec_keys_equal(&p_auth_status_1->central_kex, &p_auth_status_2->central_kex)      &&
            enc_info_equal(&p_auth_status_1->periph_keys.enc_info,
                           &p_auth_status_2->periph_keys.enc_info)                            &&
            irk_equal(&p_auth_status_1->central_keys.irk, &p_auth_status_2->central_keys.irk) &&
            addr_equal(&p_auth_status_1->central_keys.id_info,
                       &p_auth_status_2->central_keys.id_info));
}


/**@brief Connect event handler.
 *
 * @param[in]  p_ble_evt   Event received from the BLE stack.
 */
static void on_connect(ble_evt_t * p_ble_evt)
{
    m_conn_handle = p_ble_evt->evt.gap_evt.conn_handle;
    
    m_master.bond.master_handle     = INVALID_MASTER_HANDLE;
    m_master.bond.master_addr       = p_ble_evt->evt.gap_evt.params.connected.peer_addr;
    m_master.sys_attr.sys_attr_size = 0;

    if (p_ble_evt->evt.gap_evt.params.connected.irk_match)
    {
        uint8_t irk_idx  = p_ble_evt->evt.gap_evt.params.connected.irk_match_idx;
        
        if ((irk_idx >= MAX_NUM_MASTER_WHITE_LIST) ||
            (m_whitelist_irk[irk_idx].master_handle >= BLE_BONDMNGR_MAX_BONDED_MASTERS))
        {
            m_bondmngr_config.error_handler(NRF_ERROR_INTERNAL);
        }
        else
        {
            m_master = m_masters_db[m_whitelist_irk[irk_idx].master_handle];
        }
    }
    else
    {
        int i;
        
        for (i = 0; i < m_addr_count; i++)
        {
            ble_gap_addr_t *p_cur_addr = m_whitelist_addr[i].p_addr;
            
            if (memcmp(p_cur_addr->addr, m_master.bond.master_addr.addr, BLE_GAP_ADDR_LEN) == 0)
            {
                m_master = m_masters_db[m_whitelist_addr[i].master_handle];
                break;
            }
        }
    }

    if (m_master.bond.master_handle != INVALID_MASTER_HANDLE)
    {
        uint32_t err_code = master_sys_attr_set(&m_master);
        if (err_code != NRF_SUCCESS)
        {
            m_bondmngr_config.error_handler(err_code);
        }
        
        if (m_bondmngr_config.evt_handler != NULL)
        {
            ble_bondmngr_evt_t evt;
            
            evt.evt_type      = BLE_BONDMNGR_EVT_CONN_TO_BONDED_MASTER;
            evt.master_handle = m_master.bond.master_handle;
            
            m_bondmngr_config.evt_handler(&evt);
        }
    }
}


/**@brief System Attributes Missing event handler.
 *
 * @param[in]  p_ble_evt   Event received from the BLE stack.
 */
static void on_sys_attr_missing(ble_evt_t * p_ble_evt)
{
    uint32_t err_code;
    
    if (m_master.bond.master_handle == INVALID_MASTER_HANDLE)
    {
        err_code = sd_ble_gatts_sys_attr_set(m_conn_handle, NULL, 0);
    }
    else
    {
        // Current master is valid, use its data. Set the corresponding sys_attr.
        err_code = master_sys_attr_set(&m_master);
        
    }
    if (err_code != NRF_SUCCESS)
    {
        m_bondmngr_config.error_handler(err_code);
    }
}


/**@brief Update authentication status for current master.
 *
 * @details Also writes the updated bonding information to flash, and notifies the application.
 *
 * @param[in]  p_auth_status   Updated authentication status.
 */
static void auth_status_update(ble_gap_evt_auth_status_t * p_auth_status)
{
    if (!auth_status_equal(&m_master.bond.auth_status, p_auth_status))
    {
        uint32_t err_code;

        // Authentication status changed, update bonding information
        m_master.bond.auth_status        = *p_auth_status;
        m_master.bond.master_id_info.div = p_auth_status->periph_keys.enc_info.div;
        
        // Write updated bonding information to flash
        err_code = bond_info_store(&m_master.bond);
        if ((err_code == NRF_ERROR_NO_MEM) && (m_bondmngr_config.evt_handler != NULL))
        {
            ble_bondmngr_evt_t evt;
            
            evt.evt_type      = BLE_BONDMNGR_EVT_BOND_FLASH_FULL;
            evt.master_handle = m_master.bond.master_handle;
            
            m_bondmngr_config.evt_handler(&evt);
        }
        else if (err_code != NRF_SUCCESS)
        {
            m_bondmngr_config.error_handler(err_code);
        }
        
        // Pass event to the application
        if (m_bondmngr_config.evt_handler != NULL)
        {
            ble_bondmngr_evt_t evt;
        
            evt.evt_type      = BLE_BONDMNGR_EVT_AUTH_STATUS_UPDATED;
            evt.master_handle = m_master.bond.master_handle;
            
            m_bondmngr_config.evt_handler(&evt);
        }
    }
}


/**@brief Authentication Status event handler.
 *
 * @param[in]  p_ble_evt   Event received from the BLE stack.
 */
static void on_auth_status(ble_gap_evt_auth_status_t * p_auth_status)
{
    if (p_auth_status->auth_status != BLE_GAP_SEC_STATUS_SUCCESS)
    {
        return;
    }
    
    if (m_master.bond.master_handle == INVALID_MASTER_HANDLE)
    {
        uint32_t err_code = master_find_in_db(p_auth_status->periph_keys.enc_info.div);
        
        switch (err_code)
        {
            case NRF_SUCCESS:
                // Master found in the list of bonded masters. Set the corresponding sys_attr.
                err_code = master_sys_attr_set(&m_master);
                break;
                
            case NRF_ERROR_NOT_FOUND:
                // Master not found, add new master
                err_code = on_auth_status_from_new_master(p_auth_status);
                break;
                
            default:
                break;
        }
        
        if (err_code != NRF_SUCCESS)
        {
            m_bondmngr_config.error_handler(err_code);
        }
    }
    else
    {
        auth_status_update(p_auth_status);
    }
}


/**@brief Security Info Request event handler.
 *
 * @param[in]  p_ble_evt   Event received from the BLE stack.
 */
static void on_sec_info_request(ble_evt_t * p_ble_evt)
{
    uint32_t err_code;

    m_master.bond.master_id_info = p_ble_evt->evt.gap_evt.params.sec_info_request;
    
    err_code = master_find_in_db(m_master.bond.master_id_info.div);
    if (err_code == NRF_SUCCESS)
    {
        // Master found in the list of bonded master. Use the encryption info for this master.
        err_code = sd_ble_gap_sec_info_reply(m_conn_handle, 
                                          &m_master.bond.auth_status.periph_keys.enc_info, 
                                          NULL);
        if (err_code != NRF_SUCCESS)
        {
            m_bondmngr_config.error_handler(err_code);
        }
        
        // In addition set the corresponding sys_attr
        err_code = master_sys_attr_set(&m_master);
    }
    else if (err_code == NRF_ERROR_NOT_FOUND)
    {
        // New master
        err_code = sd_ble_gap_sec_info_reply(m_conn_handle, NULL, NULL);
        if (err_code != NRF_SUCCESS)
        {
            m_bondmngr_config.error_handler(err_code);
        }
        
        // Initialize the sys_attr
        err_code = sd_ble_gatts_sys_attr_set(m_conn_handle, NULL, 0);
    }
    
    if (err_code != NRF_SUCCESS)
    {
        m_bondmngr_config.error_handler(err_code);
    }
}


/**@brief Connection Security Update event handler.
 *
 * @param[in]  p_ble_evt   Event received from the BLE stack.
 */
static void on_sec_update(ble_gap_evt_conn_sec_update_t * p_sec_update)
{
    uint8_t security_mode  = p_sec_update->conn_sec.sec_mode.sm;
    uint8_t security_level = p_sec_update->conn_sec.sec_mode.lv;
    
    if (((security_mode == 1) && (security_level > 1)) || 
        ((security_mode == 2) && (security_level != 0)))
    {
        if (m_bondmngr_config.evt_handler != NULL)
        {
            ble_bondmngr_evt_t evt;
            
            evt.evt_type      = BLE_BONDMNGR_EVT_ENCRYPTED;
            evt.master_handle = m_master.bond.master_handle;
            
            m_bondmngr_config.evt_handler(&evt);
        }
    }
}


void ble_bondmngr_on_ble_evt(ble_evt_t * p_ble_evt)
{
    if (!m_is_bondmngr_initialized)
    {
        m_bondmngr_config.error_handler(NRF_ERROR_INVALID_STATE);
    }

    switch (p_ble_evt->header.evt_id)
    {
        case BLE_GAP_EVT_CONNECTED:
            on_connect(p_ble_evt);
            break;

        // NOTE: All actions to be taken on the Disconnected event are performed in
        //       ble_bondmngr_bonded_masters_store(). This function must be called from the
        //       Disconnected handler of the application before advertising is restarted (to make
        //       sure the flash blocks are cleared while the radio is inactive).
            
        case BLE_GATTS_EVT_SYS_ATTR_MISSING:
            on_sys_attr_missing(p_ble_evt);
            break;

        case BLE_GAP_EVT_AUTH_STATUS:
            on_auth_status(&p_ble_evt->evt.gap_evt.params.auth_status);
            break;
            
        case BLE_GAP_EVT_SEC_INFO_REQUEST:
            on_sec_info_request(p_ble_evt);
            break;
            
        case BLE_GAP_EVT_CONN_SEC_UPDATE:
            on_sec_update(&p_ble_evt->evt.gap_evt.params.conn_sec_update);
            break;
        
        default:
            break;
    }
}


uint32_t ble_bondmngr_bonded_masters_store(void)
{
    uint32_t err_code;
    int      i;

    if (!m_is_bondmngr_initialized)
    {
        return NRF_ERROR_INVALID_STATE;
    }

    if (m_master.bond.master_handle != INVALID_MASTER_HANDLE)
    {
        // Fetch System Attributes from stack.
        uint16_t sys_attr_size = SYS_ATTR_BUFFER_MAX_LEN;
        
        err_code = sd_ble_gatts_sys_attr_get(m_conn_handle,
                                          m_master.sys_attr.sys_attr,
                                          &sys_attr_size); 
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
        
        m_master.sys_attr.master_handle = m_master.bond.master_handle;
        m_master.sys_attr.sys_attr_size = (uint16_t)sys_attr_size;
        
        // Update current master
        err_code = master_update();
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
    }

    // Save bonding information if changed
    if (bond_info_changed())
    {
        // Erase flash page
        err_code = ble_flash_page_erase(m_bondmngr_config.flash_page_num_bond);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
    
        // Store bond information for all masters
        m_bond_info_in_flash_count = 0;
        for (i = 0; i < m_masters_in_db_count; i++)
        {
            err_code = bond_info_store(&m_masters_db[i].bond);
            if (err_code != NRF_SUCCESS)
            {
                return err_code;
            }
        }
    }
    
    // Save system attribute information if changed
    if (sys_attr_changed())
    {
        // Erase flash page
        err_code = ble_flash_page_erase(m_bondmngr_config.flash_page_num_sys_attr);
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }

        // Store system attribute information for all masters
        m_sys_attr_in_flash_count = 0;
        for (i = 0; i < m_masters_in_db_count; i++)
        {
            err_code = sys_attr_store(&m_masters_db[i].sys_attr);
            if (err_code != NRF_SUCCESS)
            {
                return err_code;
            }
        }
    }
    
    m_conn_handle                   = BLE_CONN_HANDLE_INVALID;
    m_master.bond.master_handle     = INVALID_MASTER_HANDLE;
    m_master.sys_attr.master_handle = INVALID_MASTER_HANDLE;
    m_master.sys_attr.sys_attr_size = 0;
    
    return NRF_SUCCESS;
}


uint32_t ble_bondmngr_sys_attr_store(void)
{
    uint32_t err_code;
      
    if (m_master.sys_attr.sys_attr_size  == 0) 
    {
        // Connected to new master. ence the flash block for sys attribute information for this
        // master is empty. Hence no erase is needed. 
        
        uint16_t sys_attr_size = SYS_ATTR_BUFFER_MAX_LEN;
        
        // Fetch system attributes from stack.
        err_code = sd_ble_gatts_sys_attr_get(m_conn_handle,
                                             m_master.sys_attr.sys_attr,
                                             &sys_attr_size);

        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
        
        m_master.sys_attr.master_handle = m_master.bond.master_handle;
        m_master.sys_attr.sys_attr_size = (uint16_t)sys_attr_size;
        
        // Copy the system attribute data to database.
        m_masters_db[m_masters_in_db_count].sys_attr = m_master.sys_attr;        

        // Write new master's system attributes to flash
        return (sys_attr_store(&m_master.sys_attr));
    }
    else
    {
        // Will not write to flash because system attribute info of an old master would already be
        // in flash and so this operation needs a flash erase operation.
        return NRF_ERROR_INVALID_STATE;
    }
}


uint32_t ble_bondmngr_bonded_masters_delete(void)
{
    if (!m_is_bondmngr_initialized)
    {
        return NRF_ERROR_INVALID_STATE;
    }
    
    m_masters_in_db_count         = 0;
    m_bond_info_in_flash_count    = 0;
    m_sys_attr_in_flash_count     = 0;
    
    return flash_pages_erase();
}


uint32_t ble_bondmngr_master_addr_get(int8_t master_handle, ble_gap_addr_t * p_master_addr)
{
    if (
        (master_handle == INVALID_MASTER_HANDLE) ||
        (master_handle >= m_masters_in_db_count) ||
        (p_master_addr == NULL) ||
        (m_masters_db[master_handle].bond.auth_status.central_kex.irk)
        )
    {
        return NRF_ERROR_INVALID_PARAM;
    }

    *p_master_addr = m_masters_db[master_handle].bond.master_addr;
    return NRF_SUCCESS;
}


uint32_t ble_bondmngr_whitelist_get(ble_gap_whitelist_t * p_whitelist)
{
    static ble_gap_addr_t * s_addr[MAX_NUM_MASTER_WHITE_LIST];
    static ble_gap_irk_t  * s_irk[MAX_NUM_MASTER_WHITE_LIST];

    int i;

    for (i = 0; i < m_irk_count; i++)
    {
        s_irk[i] = m_whitelist_irk[i].p_irk;
    }
    for (i = 0; i < m_addr_count; i++)
    {
        s_addr[i] = m_whitelist_addr[i].p_addr;
    }
    
    p_whitelist->addr_count = m_addr_count;
    p_whitelist->pp_addrs   = (m_addr_count != 0) ? s_addr : NULL;
    p_whitelist->irk_count  = m_irk_count;
    p_whitelist->pp_irks    = (m_irk_count != 0) ? s_irk : NULL;
    
    return NRF_SUCCESS;
}


uint32_t ble_bondmngr_init(ble_bondmngr_init_t * p_init)
{
    uint32_t err_code;

    if (p_init->error_handler == NULL)
    {
        return NRF_ERROR_INVALID_PARAM;
    }
    if (BLE_BONDMNGR_MAX_BONDED_MASTERS > MAX_BONDS_IN_FLASH)
    {
        return NRF_ERROR_DATA_SIZE;
    }
    
    m_bondmngr_config = *p_init;

    memset(&m_master, 0, sizeof(master_t));
    
    m_master.bond.master_handle   = INVALID_MASTER_HANDLE;
    m_conn_handle                 = BLE_CONN_HANDLE_INVALID;
    m_masters_in_db_count         = 0;
    m_bond_info_in_flash_count    = 0;
    m_sys_attr_in_flash_count     = 0;
    
    // Erase all stored masters if specified
    if (m_bondmngr_config.bonds_delete)
    {
        err_code = flash_pages_erase();
        if (err_code != NRF_SUCCESS)
        {
            return err_code;
        }
    }

    // Load bond manager data from flash
    err_code = load_all_from_flash();
    if (err_code != NRF_SUCCESS)
    {
        return err_code;
    }

    m_is_bondmngr_initialized = true;

    return NRF_SUCCESS;
}
