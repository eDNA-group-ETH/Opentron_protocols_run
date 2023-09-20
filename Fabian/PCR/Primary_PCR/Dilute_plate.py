

#This script doesn't really dilute the DNA it simply transfers a set volume in to a new plate 
#The receiving Plate should allready have water in the respective wells and for the respective dilution
# for a 1:5 Dilution e.g. prepare a plate with 20yl and transfer 5 yl 


from opentrons import protocol_api
from numpy import floor
from itertools import chain

metadata = {
    'apiLevel': '2.8',
    'author': 'Jon Sanders'}

# Define parameters for protocol

###### Source Plates ######

sample_plates = {'Source_plate': {'pos': 4,
                             'tip': 1}}

# Define columns to transfer


sample_cols = ['A1', 'A2','A3', 'A4', 'A5', 'A6', 
'A7', 'A8', 'A9', 'A10', 'A11', 'A12']

###### Destination Plates #######

# Define Destination plate positions.
dest_plates = {'Dest 1': 7}

###### Sample:Dest map #######

# Link each sample plate to the destination plate replicates
sample_dest_map = {'Source_plate': ['Dest 1']}

#Dest plate types
sample_labware = 'biorad_96_wellplate_200ul_pcr'
dest_labware = 'biorad_96_wellplate_200ul_pcr'

# DNA transfer volume

sample_vol = 5

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
    pipette_20.default_speed = 200


    # Dispense DNA
    for s in sample_plates:
        for c in sample_cols:
            print(sample_tips[s][c])
            pipette_20.pick_up_tip(sample_tips[s][c])
            pipette_20.distribute(sample_vol,
                                    sample_obj[s][c].bottom(z=3),
                                    [dest_obj[p][c].bottom(z=3) for p in sample_dest_map[s]],
                                    new_tip='never',
                                    blow_out=False,
                                    disposal_volume=0,
                                    trash=False)
            pipette_20.air_gap(10)                        
            pipette_20.drop_tip()
    

