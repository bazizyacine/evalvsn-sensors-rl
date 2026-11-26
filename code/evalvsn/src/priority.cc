// priority.cc - the 64 coefficients of a block, in zigzag order, split into
// priority levels along the anti-diagonals of the block (13 levels: 3, 3, 4,
// 5, 6, 7, 8, 7, 6, 5, 4, 3 and 3 coefficients, the last level taking the
// rest when fewer are asked); and the block rebuilt from its levels.

#include "evalvsn.h"

vector<prioritiesInfo> priorityEncoder(inputParameters IP, Mat_<double> blockZigZag, vector<prioritiesInfo> vecPI, prioritiesInfo PI)
{
    int levelStart = 0;

    for (int i = 1; i <= IP.priorityNb; i++)
    {
        if (i < IP.priorityNb)
        {
            switch (i)
            {
            case 1:
                PI.level = blockZigZag(Range::all(), Range(0, 3));
                break;
            case 2:
                PI.level = blockZigZag(Range::all(), Range(3, 6));
                break;
            case 3:
                PI.level = blockZigZag(Range::all(), Range(6, 10));
                break;
            case 4:
                PI.level = blockZigZag(Range::all(), Range(10, 15));
                break;
            case 5:
                PI.level = blockZigZag(Range::all(), Range(15, 21));
                break;
            case 6:
                PI.level = blockZigZag(Range::all(), Range(21, 28));
                break;
            case 7:
                PI.level = blockZigZag(Range::all(), Range(28, 36));
                break;
            case 8:
                PI.level = blockZigZag(Range::all(), Range(36, 43));
                break;
            case 9:
                PI.level = blockZigZag(Range::all(), Range(43, 49));
                break;
            case 10:
                PI.level = blockZigZag(Range::all(), Range(49, 54));
                break;
            case 11:
                PI.level = blockZigZag(Range::all(), Range(54, 58));
                break;
            case 12:
                PI.level = blockZigZag(Range::all(), Range(58, 61));
                break;
            case 13:
                PI.level = blockZigZag(Range::all(), Range(61, 64));
                break;
            }
        }
        else if (i == IP.priorityNb)
        {
            PI.level = blockZigZag(Range::all(), Range(levelStart, blockZigZag.cols));
        }

        levelStart = levelStart + PI.level.cols;

        PI.dataPriority = i;

        vecPI.push_back(PI);
    }

    return vecPI;
}

vector<prioritiesInfo> priorityDecoder(inputParameters IP, vector<prioritiesInfo> &levelsInfo, prioritiesInfo PI)
{
    int levelStart, pixelsNb, r;

    PI.blockNb = 0;

    if (PI.dataPriority < IP.priorityNb)
    {
        switch (PI.dataPriority)
        {
        case 1:
            levelStart = 0;
            pixelsNb = 3;
            break;
        case 2:
            levelStart = 3;
            pixelsNb = 3;
            break;
        case 3:
            levelStart = 6;
            pixelsNb = 4;
            break;
        case 4:
            levelStart = 10;
            pixelsNb = 5;
            break;
        case 5:
            levelStart = 15;
            pixelsNb = 6;
            break;
        case 6:
            levelStart = 21;
            pixelsNb = 7;
            break;
        case 7:
            levelStart = 28;
            pixelsNb = 8;
            break;
        case 8:
            levelStart = 36;
            pixelsNb = 7;
            break;
        case 9:
            levelStart = 43;
            pixelsNb = 6;
            break;
        case 10:
            levelStart = 49;
            pixelsNb = 5;

            break;
        case 11:
            levelStart = 54;
            pixelsNb = 4;

            break;
        case 12:
            levelStart = 58;
            pixelsNb = 3;

            break;
        case 13:
            levelStart = 61;
            pixelsNb = 3;
            break;
        }
    }
    else if (PI.dataPriority == IP.priorityNb)
    {
        switch (PI.dataPriority)
        {
        case 1:
            levelStart = 0;
            pixelsNb = 64;
            break;
        case 2:
            levelStart = 3;
            pixelsNb = 61;
            break;
        case 3:
            levelStart = 6;
            pixelsNb = 58;
            break;
        case 4:
            levelStart = 10;
            pixelsNb = 54;
            break;
        case 5:
            levelStart = 15;
            pixelsNb = 49;
            break;
        case 6:
            levelStart = 21;
            pixelsNb = 43;
            break;
        case 7:
            levelStart = 28;
            pixelsNb = 36;
            break;
        case 8:
            levelStart = 36;
            pixelsNb = 28;
            break;
        case 9:
            levelStart = 43;
            pixelsNb = 21;
            break;
        case 10:
            levelStart = 49;
            pixelsNb = 15;
            break;
        case 11:
            levelStart = 54;
            pixelsNb = 10;
            break;
        case 12:
            levelStart = 58;
            pixelsNb = 6;
            break;
        case 13:
            levelStart = 61;
            pixelsNb = 3;
            break;
        }
    }

    r = PI.level.cols % pixelsNb;

    if (r != 0)
    {
        Mat_<double> level = Mat::zeros(1, pixelsNb - r, CV_64F);
        hconcat(PI.level, level, PI.level);
    }

    for (int i = 0; i < PI.level.cols - 1; i += pixelsNb)
    {
        Mat_<double> level = Mat::zeros(1, 64, CV_64F);

        PI.blockNb++;

        PI.level(Range::all(), Range(i, i + pixelsNb)).copyTo(level(Range::all(), Range(levelStart, levelStart + pixelsNb)));

        // One entry per block, carrying what the frame assembly reads: the
        // frame, its type, the level and the block's coefficients. The bit
        // string and the offset tables of the whole level are not copied
        // into each of the level's 396 entries (some 60 000 copies of long
        // strings otherwise).
        levelsInfo.push_back({PI.sendTime, PI.frameNb, PI.frameType, PI.dataPriority, PI.dataSize, string(), PI.blockNb, level, vector<int>(), vector<int>()});
    }

    return levelsInfo;
}
