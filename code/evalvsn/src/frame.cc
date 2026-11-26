// frame.cc - a frame cut into 8x8 blocks: each block transformed, quantised,
// read in zigzag order and split into priority levels; and the inverse.

#include "evalvsn.h"

vector<prioritiesInfo> frameEncoder(inputParameters IP, Mat_<double> encodedFrame, prioritiesInfo PI)
{
    Mat_<double> block, blockZigZag;
    vector<prioritiesInfo> vecPI;

    PI.blockNb = 0;

    for (int i = 0; i <= encodedFrame.rows - 1; i += 8)
    {
        for (int j = 0; j <= encodedFrame.cols - 1; j += 8)
        {
            PI.blockNb++;
            block = encodedFrame(Range(i, i + 8), Range(j, j + 8));

            blockZigZag = zigzagEncoder(quantificationEncoder(IP, dctEncoder(block)));
            vecPI = priorityEncoder(IP, blockZigZag, vecPI, PI);
        }
    }

    return vecPI;
}

Mat_<double> frameDecoder(inputParameters IP, Mat_<double> decodedFrame)
{
    Mat_<double> blockQTF;

    for (int i = 0; i <= decodedFrame.rows - 1; i += 8)
    {
        for (int j = 0; j <= decodedFrame.cols - 1; j += 8)
        {
            blockQTF = dctDecoder(quantificationDecoder(IP, decodedFrame(Range(i, i + 8), Range(j, j + 8))));
            blockQTF.copyTo(decodedFrame(Range(i, i + 8), Range(j, j + 8)));
        }
    }

    return decodedFrame;
}
