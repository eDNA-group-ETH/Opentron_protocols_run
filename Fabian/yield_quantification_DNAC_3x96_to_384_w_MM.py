from opentrons import protocol_api
from numpy import floor
from itertools import chain

metadata = {
    'apiLevel': '2.8',
    'author': 'Jon Sanders'}

# Define parameters for protocol

###### Source Plates ######

sample_plates = {'Source_plate1': {'pos': 4,
                             'tip': 1},
                 'Source_plate2': {'pos': 5,
                             'tip': 2},
                 'Source_plate3': {'pos': 6,
                             'tip': 3},
                 'Source_plate4': {'pos': 7,
                             'tip': 10}}

# Define columns to transfer

# source plate 1 -3 are full Sample plates. Source plate 4 is to include Standards. Mark in which rows the standards (in duplicates) are.
# add Mastermix in all Wells (A1 to P12) and in every second row A13 to P24. Add additional MM in A13 and A14 (for standards).

sample_cols = {
    'Source_plate1': [1,2,3,4,5,6,7,8,9,10,11,12],
    'Source_plate2': [1,2,3,4,5,6,7,8,9,10,11,12],
    'Source_plate3': [1,2,3,4,5,6,7,8,9,10,11,12],
    'Source_plate4': [1,2],
}


###### Destination Plates #######

# Define Destination plate positions.
dest_plates = {'Dest 1': 8}

###### Sample:Dest map #######

# Link each sample plate to the destination plate replicates
sample_dest_map = {'Source_plate1': ['Dest 1'],
                   'Source_plate2': ['Dest 1'],
                   'Source_plate3': ['Dest 1'],
                   'Source_plate4': ['Dest 1']}

#Dest plate types
sample_labware = 'biorad_96_wellplate_200ul_pcr'
dest_labware = 'nunc_384_wellplate_120ul'

# DNA transfer volume

sample_vol = 2

def run(protocol: protocol_api.ProtocolContext):


    # define deck positions and labware
    sample_obj = {}
    sample_tips = {}
    pcr_obj = {}
    
    for s in sample_plates:
        sample_obj[s] = protocol.load_labware(sample_labware,
                                              sample_plates[s]['pos'],
                                              s)
        sample_tips[s] = protocol.load_labware('opentrons_96_filtertiprack_20ul',
                                              sample_plates[s]['tip'],
                                              s)

    # destination plates
    dest_obj = {}
    
    for p in dest_plates:
        dest_obj[p] = protocol.load_labware(dest_labware,
                                           dest_plates[p],
                                           p)

    # initialize pipettes
    pipette_20 = protocol.load_instrument('p20_multi_gen2',
                                             'right')
                                             
    # decrease movement speed
    pipette_20.default_speed = 300
    


    # Dispense DNA   

    dest_positions = {
        'Source_plate1': [("A", 0)],
        'Source_plate2': [("B", 0)],
        'Source_plate3': [("A", 12)],
        'Source_plate4': [("B", 12)]
    }


                
    for s in sample_plates:            
        for p in sample_dest_map[s]:
            for c in sample_cols[s]:
                pipette_20.pick_up_tip(sample_tips[s]["A"+str(c)])
                
                dest_wells = [
                        dest_obj[p][row + str(c + col_offset)].bottom(z=0.2)
                        for row, col_offset in dest_positions[s]
                    ]
                
                
                aspirate_vol = sample_vol*len(dest_wells)
                
                pipette_20.aspirate(aspirate_vol, sample_obj[s]["A"+str(c)].bottom(z=0.1))

                for well in dest_wells:
                    pipette_20.dispense(sample_vol, well)

                pipette_20.air_gap(10)
                pipette_20.default_speed = 300
                pipette_20.drop_tip()


