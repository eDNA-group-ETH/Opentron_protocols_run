from opentrons import protocol_api
from numpy import floor
from itertools import chain

metadata = {
    'apiLevel': '2.8',
    'author': 'Jon Sanders'}

# Define parameters for protocol

###### Source Plates ######

sample_plates = {'Source_plate': {'pos': 1,
                             'tip': 2}}

# Define columns to transfer


sample_cols = [1,2,3,4,5,6,7,8,9,10,11,12]

###### Destination Plates #######

# Define Destination plate positions.
dest_plates = {'Dest 1': 4}

###### Sample:Dest map #######

# Link each sample plate to the destination plate replicates
sample_dest_map = {'Source_plate': ['Dest 1']}

#Dest plate types
sample_labware = 'biorad_96_wellplate_200ul_pcr'
dest_labware = 'biorad_384_wellplate_50ul'

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
    for s in sample_plates:
        for p in sample_dest_map[s]:
            for c in sample_cols:
                #print(sample_tips[s][c])
                pipette_20.pick_up_tip(sample_tips[s]["A"+str(c)])
                
                dest_wells = [
                dest_obj[p][row + str(c + col_offset)].bottom(z=0.2)
                for row, col_offset in [("A", 0), ("B", 0), ("A", 12)]
            ]
                pipette_20.default_speed = 100
                pipette_20.distribute(sample_vol,
                                    sample_obj[s]["A"+str(c)].bottom(z=0.1),
                                    dest_wells,
                                    new_tip='never',
                                    blow_out=False,
                                    disposal_volume=0,
                                    trash=False)
                pipette_20.air_gap(10)  
                pipette_20.default_speed = 300                
                pipette_20.drop_tip()
                
            
    
