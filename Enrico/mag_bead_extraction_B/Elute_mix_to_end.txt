import sys
sys.path.append("/root/opentrons_functions/opentrons_functions")

from opentrons import protocol_api

from magbeads import(remove_supernatant, bead_wash, bead_mix)
    
from transfer import add_buffer


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
    cols = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
    'A7', 'A8', 'A9', 'A10', 'A11', 'A12']
    
else:
    pause_eth_bind = 10*60
    pause_aq_bind = 20*60
   # pause_dry = 5*60 #manual pause to make sure everything is really dry
    pause_elute = 5*60

    # Limit columns
    cols = ['A1','A2', 'A3', 'A4', 'A5', 'A6',
            'A7', 'A8']
    # cols = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
    #         'A7', 'A8', 'A9', 'A10', 'A11', 'A12']


# Lysate transfer volume

lysate_vol = 900

wash_vol = 290

rinse_vol = 800

elute_vol = 50

elute_mix_num = 15

# fill volumes

eth_well_vol = 40000

hyb_well_vol = 40000

# define magnet engagement height for plates
# (none if using labware with built-in specs)
mag_engage_height = 9


# REAGENTS plate:
# Bead columns
bead_cols = ['A1','A2']

# Elute col
elute_col = 'A6'


# WASH plate:

# Ethanol columns
eth_cols = ['A1','A2', 'A3', 'A4']


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
    tiprack_buffers = protocol.load_labware('opentrons_96_tiprack_300ul',
                                            7)
    tiprack_elution = protocol.load_labware(
                            'opentrons_96_filtertiprack_200ul', 4)
    tiprack_wash1 = protocol.load_labware('opentrons_96_tiprack_300ul',
                                          1)
    tiprack_wash2 = protocol.load_labware('opentrons_96_tiprack_300ul',
                                          8)
    # tiprack_wash3 = protocol.load_labware('opentrons_96_tiprack_300ul',
    #                                       9)
    # tiprack_wash4 = protocol.load_labware('opentrons_96_tiprack_300ul',
    #                                       4)

    # plates
    eluate = protocol.load_labware('biorad_96_wellplate_200ul_pcr',
                                   10, 'eluate')
    waste = protocol.load_labware('nest_1_reservoir_195ml',
                                  9, 'liquid waste')
    reagents = protocol.load_labware('brand_6_reservoir_40000ul',
                                     2, 'reagents')
    wash = protocol.load_labware('brand_6_reservoir_40000ul',
                                     5, 'wash buffers')

    samples = protocol.load_labware('thermoscientificnunc_96_wellplate_2000ul',
                                     3, 'samples')
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


    ### Adding beads

    hyb_vol = 0.66 * lysate_vol


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
        pipette_left.touch_tip()
        # we'll use these same tips for final transfer
        pipette_left.return_tip()
        # t_mix = clock() - t0

    # bind to magnet
    protocol.comment('Binding beads to magnet.')

    magblock.engage(height_from_base=mag_engage_height)

    protocol.delay(seconds=pause_aq_bind)

    protocol.comment('Transferring eluted DNA to final plate.')
    for col in cols:
        pipette_left.pick_up_tip(tiprack_elution.wells_by_name()[col])
        pipette_left.aspirate(elute_vol,
                              mag_plate[col].bottom(z=2),
                              rate=bead_flow)
        pipette_left.dispense(elute_vol, eluate[col].bottom(z=2))
        # pipette_left.blow_out(eluate[col].top(z=-1))
        # pipette_left.touch_tip()
        # we're done with these tips now
        pipette_left.drop_tip()

    magblock.disengage()