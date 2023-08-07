import sys
import os

sys.path.append("/root/opentrons_functions/opentrons_functions")
sys.path.append("/Users/fabian/Documents/01_Work/03_Docs/Opentron/opentrons_functions/opentrons_functions")
sys.path.append(os.path.join('C:\\','Users','localadmin','Documents','GitHub','opentrons_functions','opentrons_functions'))

from opentrons import protocol_api

from magbeads import(remove_supernatant, bead_wash, bead_mix)
    
from transfer import add_buffer

from numpy import ceil


metadata = {'apiLevel': '2.8',
            'author': 'Jon Sanders'}

# Set to `True` to perform a short run, with brief pauses and only
# one column of samples
test_run = False

if test_run:
    pause_eth_bind = 5
    pause_aq_bind = 3
    pause_dry = 5
    pause_elute = 5

    # Limit columns
    cols = ['A1']
    
else:
    pause_eth_bind = 5*60
    pause_aq_bind = 20*60
   # pause_dry = 5*60 #manual pause to make sure everything is really dry
    pause_elute = 5*60

    # Limit columns
    cols = ['A1', 'A2','A3', 'A4', 'A5', 'A6',
             'A7', 'A8', 'A9', 'A10','A11', 'A12']
    # cols = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
    #         'A7', 'A8', 'A9', 'A10', 'A11', 'A12']


# Lysate transfer volume

lysate_vol = 800

wash_vol = 290

rinse_vol = 1.75*lysate_vol

elute_vol = 200 #total volume

elut_plate = 1 #if elut_plate > 1 the volume is split equally on elut_plate plates (max 3)

if elut_plate not in [1,2,3]:
    raise Exception("you must have either one, two or three elution plates")

elute_mix_num = 2

# fill volumes

eth_well_vol = 35000

hyb_well_vol = 20000

# define magnet engagement height for plates
# (none if using labware with built-in specs)
mag_engage_height = 9


# BEAD plate:
# Bead columns 20 ml in each
bead_cols = ['A3','A4', 'A5','A6']

# Elute col
elute_col = 'A1'

# Elute and Wash plate:

# Ethanol columns 40 ml in each
eth_cols = ['A1','A2','A3', 'A4', 'A5','A6']


# bead aspiration flow rate
bead_flow = .25

# bead mix flow rate
mix_rate = 2

# wash mix mutliplier
wash_mix = 5


# function relating volume to liquid height in magplate
def vol_fn(x):
    return(x/(3.14 * 3**2))


def run(protocol: protocol_api.ProtocolContext):

    # ### Setup

    # define deck positions and labware

    # define hardware modules
    magblock = protocol.load_module('magnetic module', 6)
    magblock.disengage()

    # tips
    tiprack_buffers = protocol.load_labware('opentrons_96_filtertiprack_200ul',
                                            1)
    tiprack_elution = protocol.load_labware(
                            'opentrons_96_filtertiprack_200ul', 4)
    tiprack_wash1 = protocol.load_labware('opentrons_96_filtertiprack_200ul',
                                          7)
    # tiprack_wash2 = protocol.load_labware('opentrons_96_tiprack_300ul',
                                          # 8)
    # tiprack_wash3 = protocol.load_labware('opentrons_96_tiprack_300ul',
    #                                       9)
    # tiprack_wash4 = protocol.load_labware('opentrons_96_tiprack_300ul',
    #                                       4)

    # plates
    
    eluate1 = protocol.load_labware('biorad_96_wellplate_200ul_pcr',
                                   10, 'eluate1')
                                   
    if elut_plate > 1:
        eluate2 = protocol.load_labware('biorad_96_wellplate_200ul_pcr',
                                  11, 'eluate2')
                                  
    if elut_plate > 2:
        eluate3 = protocol.load_labware('biorad_96_wellplate_200ul_pcr',
                                   8, 'eluate3')
                                   
    waste = protocol.load_labware('nest_1_reservoir_195ml',
                                  9, 'liquid waste')
    reagents = protocol.load_labware('brand_6_reservoir_40000ul',
                                     2, 'reagents')
    wash = protocol.load_labware('brand_6_reservoir_40000ul',
                                     5, 'wash buffers')

    samples = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul',
                                     3, 'samples')
    # load plate on magdeck
    
    mag_plate = magblock.load_labware('thermoscientificnunc_96_wellplate_2000ul')

    # initialize pipettes
    pipette_left = protocol.load_instrument('p300_multi_gen2',
                                            'left',
                                            tip_racks=[tiprack_buffers])

    # SeraMag bead wells
    bead_wells = [reagents[x] for x in bead_cols]

    # Ethanol columns
    eth_wells = [wash[x] for x in eth_cols]

    # temporarily decrease movement speed to minimize mess
    pipette_left.default_speed = 200
    
    # change dispense height so tips do never tip into waste
    
    ### transfer clear lysate from sample to magplate, avoiding the pellet
    

    
    # This should:
    # - disengage magnet
    # - pick up tip from position 6
    # - pick up reagents from column 2 of position 9
    # - dispense into magplate
    # - mix 10 times
    # - blow out, touch tip
    # - return tip to position 6
    # - wait (5 seconds)
    # - engage magnet
    # - wait (5 seconds)
    # - pick up tip from position 6
    # - aspirate from magplate
    # - dispense to position 3
    # - trash tip

    # transfer elution buffer to mag plate
    magblock.disengage()

    # add elution buffer and mix
 
 # pipet mix
    for col in cols:
        pipette_left.pick_up_tip(tiprack_elution.wells_by_name()[col])
        pipette_left.aspirate(elute_vol, reagents[elute_col], rate=1)
        pipette_left.dispense(elute_vol, mag_plate[col].bottom(z=1))
        pipette_left.mix(elute_mix_num,
                         elute_vol - 10,
                         mag_plate[col].bottom(z=1),
                         rate=mix_rate)
        pipette_left.blow_out(mag_plate[col].top())
        pipette_left.touch_tip(speed = 30,
                               radius = 0.5,
                               v_offset = -6)
        # we'll use these same tips for final transfer
        pipette_left.return_tip()

    protocol.delay(seconds=pause_elute)
    # # start timer
    # t0 = clock()
    # # mix again
    # t_mix = 0
    # while t_mix < pause_elute():
    for col in cols:
        pipette_left.pick_up_tip(tiprack_elution.wells_by_name()[col])
        pipette_left.mix(elute_mix_num,
                         elute_vol - 10,
                         mag_plate[col].bottom(z=1),
                         rate=mix_rate)
        pipette_left.blow_out(mag_plate[col].top())
        pipette_left.touch_tip(speed = 30,
                               radius = 0.5,
                               v_offset = -6)
        # we'll use these same tips for final transfer
        pipette_left.return_tip()
        # t_mix = clock() - t0

    # bind to magnet
    protocol.comment('Binding beads to magnet.')

    magblock.engage(height_from_base=mag_engage_height)

    protocol.delay(seconds=pause_aq_bind/4)
    
    #wash tips in eluate while magnet enganged
    
    for col in cols:
        pipette_left.pick_up_tip(tiprack_elution.wells_by_name()[col])
        pipette_left.mix(2,
                         elute_vol/2,
                         mag_plate[col].bottom(z=3),
                         rate=mix_rate/2)
        pipette_left.blow_out(mag_plate[col].top())
        pipette_left.touch_tip(speed = 30,
                               radius = 0.5,
                               v_offset = -6)
        # we'll use these same tips for final transfer
        pipette_left.return_tip()
    
     
    protocol.comment('Transferring eluted DNA to final plate.')
    
    for n in range(0, elut_plate):
        
        plate_list = [eluate1]
        
        if elut_plate > 1:
            plate_list = [eluate1,eluate2]
            
        if elut_plate > 2:
            plate_list = [eluate1,eluate2,eluate3]
            
    
        for col in cols:
            pipette_left.pick_up_tip(tiprack_elution.wells_by_name()[col])
            pipette_left.aspirate((elute_vol-(0.1*elute_vol))/elut_plate,
                                  mag_plate[col].bottom(z=2),
                                  rate=bead_flow)
            pipette_left.dispense(elute_vol, plate_list[n][col].bottom(z=2))
            # pipette_left.blow_out(eluate[col].top(z=-1))
            # pipette_left.touch_tip()
            # we're done with these tips now
            pipette_left.return_tip()

    magblock.disengage()