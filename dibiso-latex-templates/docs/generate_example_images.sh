#!/bin/bash

echo "Generating example images from the compiled PDFs for the README..."
mkdir -p images/biso-example
mkdir -p images/pubpart-example

echo "Clean output image directories for:"
echo "BiSO..."
rm images/biso-example/biso-example*
echo "PubPart..."
rm images/pubpart-example/pubpart-example*
echo "Done."
echo ""

echo "Generating png single images for:"
echo "BiSO..."
gs -dNOPAUSE -sDEVICE=png16m -r50 -sOutputFile=images/biso-example/biso-example-%02d.png ../examples/biso/biso-main.pdf -c quit
echo "PubPart..."
gs -dNOPAUSE -sDEVICE=png16m -r50 -sOutputFile=images/pubpart-example/pubpart-example-%02d.png ../examples/pubpart/pubpart-main.pdf -c quit
echo "Done."
echo ""

echo "Generating matrix image with borders for:"
echo "BiSO..."
montage images/biso-example/biso-example-[0-9][0-9].png -tile 2x -border 3 -geometry +10+10 images/biso-example/biso-example.png
echo "PubPart..."
montage images/pubpart-example/pubpart-example-[0-9][0-9].png -tile 2x -border 3 -geometry +10+10 images/pubpart-example/pubpart-example.png
echo "Done."
echo ""

echo "Clean temporary images for:"
echo "BiSO..."
rm images/biso-example/biso-example-*
echo "PubPart..."
rm images/pubpart-example/pubpart-example-*
echo "Done."
echo ""

echo "DONE. Example images generated."
