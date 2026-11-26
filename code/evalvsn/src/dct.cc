// dct.cc - the classical two-dimensional DCT of an 8x8 block, forward and
// inverse, computed from its definition.

#include "evalvsn.h"

Mat_<double> dctEncoder(Mat_<double> block)
{
    Mat_<double> blockDCT = Mat::zeros(block.rows, block.cols, CV_64F);
    double Cx, Cy, SUMij;

    for (int x = 0; x <= block.rows - 1; x++)
    {
        for (int y = 0; y <= block.cols - 1; y++)
        {
            SUMij = 0;
            for (int i = 0; i <= block.rows - 1; i++)
            {
                for (int j = 0; j <= block.cols - 1; j++)
                {
                    SUMij = SUMij + block.at<double>(i, j) * cos(((2.0 * j + 1.0) * y * CV_PI) / (2.0 * block.cols)) * cos(((2.0 * i + 1.0) * x * CV_PI) / (2.0 * block.rows));
                }
            }
            if (x == 0 && y == 0)
            {
                Cx = sqrt(1.0 / block.rows);
                Cy = sqrt(1.0 / block.cols);
            }
            else if (x > 0 && y == 0)
            {
                Cx = sqrt(2.0 / block.rows);
                Cy = sqrt(1.0 / block.cols);
            }
            else if (x == 0 && y > 0)
            {
                Cx = sqrt(1.0 / block.rows);
                Cy = sqrt(2.0 / block.cols);
            }
            else if (x > 0 && y > 0)
            {
                Cx = sqrt(2.0 / block.rows);
                Cy = sqrt(2.0 / block.cols);
            }
            blockDCT.at<double>(x, y) = Cx * Cy * SUMij;
        }
    }

    return blockDCT;
}

Mat_<double> dctDecoder(Mat_<double> blockDCT)
{
    Mat_<double> block = Mat::zeros(blockDCT.rows, blockDCT.cols, CV_64F);
    double Cx, Cy, SUMxy;

    for (int i = 0; i <= blockDCT.rows - 1; i++)
    {
        for (int j = 0; j <= blockDCT.cols - 1; j++)
        {
            SUMxy = 0;

            for (int x = 0; x <= blockDCT.rows - 1; x++)
            {
                for (int y = 0; y <= blockDCT.cols - 1; y++)
                {
                    if (x == 0 && y == 0)
                    {
                        Cx = sqrt(1.0 / blockDCT.rows);
                        Cy = sqrt(1.0 / blockDCT.cols);
                    }
                    else if (x > 0 && y == 0)
                    {
                        Cx = sqrt(2.0 / blockDCT.rows);
                        Cy = sqrt(1.0 / blockDCT.cols);
                    }
                    else if (x == 0 && y > 0)
                    {
                        Cx = sqrt(1.0 / blockDCT.rows);
                        Cy = sqrt(2.0 / blockDCT.cols);
                    }
                    else if (x > 0 && y > 0)
                    {
                        Cx = sqrt(2.0 / blockDCT.rows);
                        Cy = sqrt(2.0 / blockDCT.cols);
                    }

                    SUMxy = SUMxy + Cx * Cy * blockDCT.at<double>(x, y) * cos(((2.0 * j + 1.0) * y * CV_PI) / (2.0 * blockDCT.cols)) * cos(((2.0 * i + 1.0) * x * CV_PI) / (2.0 * blockDCT.rows));
                }
            }

            block.at<double>(i, j) = SUMxy;
        }
    }

    return block;
}
