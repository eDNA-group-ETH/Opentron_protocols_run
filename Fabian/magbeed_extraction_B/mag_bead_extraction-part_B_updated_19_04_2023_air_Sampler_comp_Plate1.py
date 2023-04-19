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
    pause_eth_bind = 10*60
    pause_aq_bind = 20*60
   # pause_dry = 5*60 #manual pause to make sure everything is really dry
    pause_elute = 5*60

    # Limit columns
    cols = ['A1', 'A2','A3', 'A4', 'A5', 'A6',
             'A7', 'A8', 'A9', 'A10']
    # cols = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
    #         'A7', 'A8', 'A9', 'A10', 'A11', 'A12']


# Lysate transfer volume

lysate_vol = 800

wash_vol = 290

rinse_vol = 1.75*lysate_vol

elute_vol = 200 #total volume

elut_plate = 4 #if elut_plate > 1 the volume is split equally on elut_plate plates (max 3)

if elut_plate not in [1,2,3,4]:
    raise Exception("you must have either one, two, three or four elution plates")

elute_mix_num = 2

# fill volumes

eth_well_vol = 35000

hyb_well_vol = 20000

# define magnet engagement height for plates
# (none if using labware with built-in specs)
mag_engage_height = 9


# BEAD plate:
# Bead columns 20 ml in each
bead_cols = ['A3','A4', 'A5']

# Elute col
elute_col = 'A1'

# Elute and Wash plate:

# Ethanol columns 40 ml in each
eth_cols = ['A1','A2','A3', 'A4', 'A5']


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
                                          2)
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
    
    if elut_plate > 3:
        eluate4 = protocol.load_labware('biorad_96_wellplate_200ul_pcr',
                                   7, 'eluate4')
                                   
    waste = protocol.load_labware('nest_1_reservoir_195ml',
                                  9, 'liquid waste')
    reagents = protocol.load_labware('brand_6_reservoir_40000ul',
                                     3, 'reagents')
    wash = protocol.load_labware('brand_6_reservoir_40000ul',
                                     5, 'wash buffers')

    # samples = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul',
    #                                 3, 'samples')
    # load plate on magdeck
    # mag_plate = magblock.load_labware('vwr_96_wellplate_1000ul')
    
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
    


    ### Adding beads

    hyb_vol = 0.75 * lysate_vol

    bead_mix(pipette_left,
             reagents,
             bead_cols,
             None,
             n=6,
             z_offset=2,
             mix_vol=200,
             mix_lift=20,
             mix_rate=mix_rate,
             drop_tip=True)
             

   # add beads
    bead_remaining, bead_wells = add_buffer(pipette_left,
                                            bead_wells,
                                            mag_plate,
                                            cols,
                                            hyb_vol,
                                            hyb_well_vol/8,
                                            protocol,
                                            pause_in_sec = 2,
                                            touch_tip_speed = 30,
                                            touch_tip_radius = 0.5,
                                            touch_tip_v_offset = -6,
                                            tip_vol=200,
                                            touch_tip = True,
                                            drop_tip = True)

     # mix while binding
    for i in range(0, 2): 

        for col in cols:
            pipette_left.pick_up_tip(tiprack_wash1.wells_by_name()[col])
        
            for n in range(0,2): 
                pipette_left.aspirate(190,
                                      mag_plate.wells_by_name()[col].bottom(z=5),
                                      rate = 0.5
                                     )
                pipette_left.dispense(190,
                                      mag_plate.wells_by_name()[col].bottom(z=20),
                                      rate = 0.5)
                                      
            pipette_left.touch_tip(speed = 30,
                                   radius = 0.5,
                                   v_offset = -6)                            
                                      
            pipette_left.return_tip()
        
    protocol.delay(seconds=5*60)

    # ### Prompt user to place plate on rotator
    # protocol.pause('Seal sample plate and place on rotator. Rotate at low '
                   # 'speed for 10 minutes. Then gently spin down plate, unseal, and place back on '
                   # 'position 3.')


    # # add samples
    
    subset_vol = (lysate_vol+hyb_vol)

    # # transfer to magnet
    # tip_vol=270 #for some reason it complains if we set the tip volume to 300
    # transfers = int(ceil(subset_vol / (tip_vol - 10)))
    # transfer_vol = subset_vol / transfers

    # for col in cols:
        # pipette_left.pick_up_tip(tiprack_wash1.wells_by_name()[col])
        
        # for i in range(0, transfers):
            
            # pipette_left.aspirate(transfer_vol, samples.wells_by_name()[col].bottom(z = 3))

            # pipette_left.air_gap(5)
            
            # protocol.delay(seconds=1)
            # pipette_left.touch_tip(speed = 30,
                                   # radius = 0.5,
                                   # v_offset = -6)
            
            # pipette_left.dispense(transfer_vol+10, mag_plate.wells_by_name()[col])
            
            # pipette_left.air_gap(10)
            
            # pipette_left.touch_tip(speed = 30,
                                   # radius = 0.5,
                                   # v_offset = -6)
                            
        # pipette_left.return_tip()
    

    # bind to magnet
    protocol.comment('Binding beads to magnet.')
    
    magblock.engage(height_from_base=mag_engage_height)
    
    protocol.delay(seconds=pause_aq_bind/4)
    
    for i in range(0, 2): 

        for col in cols:
            pipette_left.pick_up_tip(tiprack_wash1.wells_by_name()[col])
        
            for n in range(0,2): 
                pipette_left.aspirate(190,
                                      mag_plate.wells_by_name()[col].bottom(z=5),
                                      rate = 0.5
                                     )
                pipette_left.dispense(190,
                                      mag_plate.wells_by_name()[col].bottom(z=20),
                                      rate = 0.5)
                                      
            pipette_left.touch_tip(speed = 30,
                                   radius = 0.5,
                                   v_offset = -6)                            
                                      
            pipette_left.return_tip()
        
        protocol.delay(seconds=pause_aq_bind/4)

    # protocol.delay(seconds=pause_aq_bind/4)

    # remove supernatant
    remove_supernatant(pipette_left,
                       mag_plate,
                       cols,
                       tiprack_wash1,
                       waste['A1'],
                       super_vol=subset_vol - 5,
                       tip_vol_rs=200,
                       rate=bead_flow,
                       bottom_offset=3,
                       drop_tip=False)
                       
    # ### Prompt user to place plate on rotator
    protocol.pause('Add Plate with Etahnol in position 5')

    # Rinse well with ethanol

    eth_remaining, eth_wells = add_buffer(pipette_left,
                                          eth_wells,
                                          mag_plate,
                                          cols,
                                          rinse_vol,
                                          eth_well_vol/8,
                                          protocol,
                                          pause_in_sec = 0,
                                          touch_tip_speed = 50,
                                          touch_tip_radius = 0.75,
                                          touch_tip_v_offset = -3,
										  tip_vol= 200,
                                          tip=None,
                                          touch_tip = False)

    remove_supernatant(pipette_left,
                       mag_plate,
                       cols,
                       tiprack_wash1,
                       waste['A1'],
                       super_vol=rinse_vol - wash_vol,
                       tip_vol_rs=200,
                       rate=1,
                       bottom_offset=1,
                       drop_tip=False)

    # ### Do first wash: Wash 290 µL EtOH
    protocol.comment('Doing wash #1.')
    eth_remaining, eth_wells = bead_wash(
                                       # global arguments
                                       protocol,
                                       magblock,
                                       pipette_left,
                                       mag_plate,
                                       cols,
                                       # super arguments
                                       waste['A1'],
                                       tiprack_wash1,
                                       # wash buffer arguments
                                       eth_wells,
                                       eth_well_vol/8,
                                       # mix arguments
                                       tiprack_wash1,
                                       drop_mix_tip=False,
                                       # optional arguments,
                                       wash_vol=wash_vol,
                                       super_vol=wash_vol,
                                       super_tip_vol=200,
                                       super_blowout=True,
                                       drop_super_tip=False,
                                       rate=1,
                                       vol_fn=vol_fn,
                                       mix_n=wash_mix*2,
                                       mix_vol=190,
                                       mix_lift=0,
                                       mix_rate=mix_rate*2,
                                       remaining=eth_remaining,
                                       mag_engage_height=mag_engage_height,
                                       pause_s=pause_eth_bind)

    # iterate to next full well
    # if eth_remaining < eth_well_vol:
      #   eth_wells.pop(0)

    # protocol.pause('Replace empty tip box in position 9 with new tips.')

    # ### Do second wash: Wash 290 µL EtOH
    protocol.comment('Doing wash #2.')
    eth_remaining, eth_wells = bead_wash(
                                       # global arguments
                                       protocol,
                                       magblock,
                                       pipette_left,
                                       mag_plate,
                                       cols,
                                       # super arguments
                                       waste['A1'],
                                       tiprack_wash1,
                                       # wash buffer arguments
                                       eth_wells,
                                       eth_well_vol/8,
                                       # mix arguments
                                       tiprack_wash1,
                                       drop_mix_tip=False,
                                       # optional arguments,
                                       wash_vol=wash_vol - 50,
                                       super_vol=wash_vol,
                                       super_tip_vol=200,
                                       super_blowout=True,
                                       drop_super_tip=False,
                                       rate=1,
                                       vol_fn=vol_fn,
                                       mix_n=wash_mix*2,
                                       mix_vol=190,
                                       mix_lift=0,
                                       mix_rate=mix_rate*2,
                                       remaining=eth_remaining,
                                       mag_engage_height=mag_engage_height,
                                       pause_s=pause_eth_bind)

    # ### Dry
    protocol.comment('Removing wash and drying beads.')

    # This should:
    # - pick up tip in position 8
    # - pick up supernatant from magplate
    # - dispense in waste, position 11
    # - repeat
    # - trash tip
    # - leave magnet engaged

    # protocol.pause('Replace empty tip box in position 4 with new tips.')

    # remove supernatant
    remove_supernatant(pipette_left,
                       mag_plate,
                       cols,
                       tiprack_wash1,
                       waste['A1'],
                       super_vol=wash_vol,
                       tip_vol_rs=200,
                       rate=bead_flow,
                       bottom_offset=.5,
                       drop_tip=False)
                       
                       # remove supernatant
    remove_supernatant(pipette_left,
                       mag_plate,
                       cols,
                       tiprack_wash1,
                       waste['A1'],
                       super_vol=wash_vol,
                       tip_vol_rs=200,
                       rate=bead_flow,
                       bottom_offset=.2,
                       drop_tip=True)

    # dry
   # protocol.delay(seconds=pause_dry)
                    
    protocol.comment('Drying - resume manually (20 min or when dry)')
    
    ### Prompt user to manually check if all ethanol has been removed
    protocol.pause( 'Check if all Ethanol has been successfull removed - '
                    'if not, remove by hand')

    # ### Elute
    protocol.comment('Eluting DNA from beads.')
    
     # ### Prompt user to place plate on rotator
    protocol.pause('Make sure there are not Ethanol drops in Plate!'
    'Add elution buffer to well A1 of Plate on Position 3 (same as beads)')
    
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
        
        plate_list = [eluate1,eluate2,eluate3,eluate4]
    
        for col in cols:
            pipette_left.pick_up_tip(tiprack_elution.wells_by_name()[col])
            pipette_left.aspirate((elute_vol-10)/elut_plate,
                                  mag_plate[col].bottom(z=1),
                                  rate=bead_flow)
            pipette_left.dispense(elute_vol, plate_list[n][col].bottom(z=2))
            # pipette_left.blow_out(eluate[col].top(z=-1))
            # pipette_left.touch_tip()
            # we're done with these tips now
            pipette_left.return_tip()

    magblock.disengage()