# FussyBin

Code for FussyBin — an IoT appliance that uses machine vision to categorise your rubbish and sort it into the correct bin. Created for the [o1 Bridge hackathon](https://www.o1lab.space/).

An ESP32-CAM captures an image of the item being discarded, which is classified using a vision model. The result drives a servo mechanism that directs the rubbish into the correct bin (recycling, compost, or landfill).

**Stack:** MicroPython (ESP32), Python (host scripts), OpenCLIP (ViT-B-32).
