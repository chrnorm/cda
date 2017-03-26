# cda
A deep learning crater detection algorithm

# Installation
Run "downloadimages.sh" to fetch the THEMIS mosaics from USGS via wget.
Run "cropimg.sh" to split the THEMIS mosaics into tiles (requires ImageMagick to be installed)

# Usage
Run generate_cratersets.py in the preprocessing folder as follows:
  $python generate_cratersets.py cfg/truth.cfg

Then train the model by running train.py in the tensorbox folder as follows:
  $python train.py --hypes hypes/overfeat_resnet_rezoom_cda.json --gpu 0 --logdir output

(note - need to change the path names in both the train.py command and also the JSON file in future commit)

# Todos
Double check installation scripts run without issue
Make preprocessing / training workflow simpler
