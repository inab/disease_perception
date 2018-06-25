#!/bin/bash

convert -density 384 -background transparent disease_perception_icon.svg -define icon:auto-resize=256,128,64,32,16 ../FRONTEND/app/images/disease_perception.ico
