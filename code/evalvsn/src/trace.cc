// trace.cc - the traces of the encoding: st-priority.dat (one line per
// packet of each frame and level) and st-frame.dat (one line per frame), the
// levels rebuilt from the packets of a trace.

#include "evalvsn.h"

void traceEncoder(inputParameters IP, vector<prioritiesInfo> vecPI, vector<framesInfo> vecFI, string priorityName, string frameName)
{
    prioritiesInfo PI;
    framesInfo FI;
    ofstream priorityTrace, frameTrace;
    int levelZeros;

    priorityTrace.open(priorityName, ofstream::app);

    PI.dataSize = FI.frameSize = PI.dataPriority = 0;

    for (int i = 1; i <= IP.priorityNb; i++)
    {
        Mat_<double> levels;

        for (int j = 0; j <= ((int)vecPI.size()) - 1; j++)
        {
            if (vecPI[j].dataPriority == i)
            {
                PI.sendTime = vecPI[j].sendTime;
                PI.frameNb = vecPI[j].frameNb;
                PI.frameType = vecPI[j].frameType;
                PI.dataPriority = vecPI[j].dataPriority;
                PI.blockNb = vecPI[j].blockNb;

                if (levels.empty())
                {
                    levels = vecPI[j].level;
                }
                else if (!(levels.empty()))
                {
                    hconcat(levels, vecPI[j].level, levels);
                }
            }
        }

        PI.level = levels;

        levelZeros = levelZerosEvaluate(PI.level);

        if (levelZeros != PI.level.cols)
        {
            PI = rleEncoder(PI);

            Mat_<double> elems = PI.level.clone();

            // The code-word tables are the level's own: PI serves every
            // level of the frame in turn.
            PI.levelSize.clear();
            PI.levelOffset.clear();
            PI.data.clear();
            PI = expGolombEncoder(PI);

            // One line per packet: each packet of the level, cut on the code
            // words, its coefficient index in its first two bytes.
            // st-packetGenerate.sh then sends each line as one packet.
            for (const string &unit : packetEncoder(IP, PI, elems))
            {
                PI.dataSize = ((int)unit.length()) / 2;
                FI.frameSize += PI.dataSize;
                if (PI.dataPriority)
                {
                    priorityTrace << PI.sendTime << '\t' << PI.frameNb << '\t' << PI.frameType << '\t' << PI.dataPriority << '\t' << PI.dataSize << '\t' << unit << '\n';
                }
            }

            PI.dataPriority = PI.dataSize = 0;

            PI.data.clear();
        }
    }

    priorityTrace.close();

    frameTrace.open(frameName, ofstream::app);

    for (int i = 0; i <= ((int)vecFI.size()) - 1; i++)
    {
        frameTrace << vecFI[i].frameNb << '\t' << vecFI[i].frameType << '\t' << FI.frameSize << '\n';
    }

    frameTrace.close();
}

vector<prioritiesInfo> traceDecoder(inputParameters IP, string unitsName, bool received)
{
    // The packets of each frame and level: every packet of st-priority.dat
    // for the reference decoding, the payloads that reached the sink (the
    // deduplicated reception trace) for the decoding after the network. The
    // decoder reads nothing else of the sender.
    map<pair<int, int>, vector<string>> units;
    map<pair<int, int>, prioritiesInfo> heads;
    ifstream trace(unitsName, ifstream::in);
    stringstream lineStream;
    string line;
    while (getline(trace, line, '\n'))
    {
        if (line.empty() || line[0] == '#')
            continue;
        prioritiesInfo PI;
        string data;
        lineStream.str(line);
        lineStream.clear();
        if (received)
        {
            packetsInfo PK;
            lineStream >> PK.sTime >> PK.seqNb >> PK.pSize >> PK.frameNb >> PK.frameType >> PK.prioNb >> PK.offset >> data;
            PI.sendTime = PK.sTime;
            PI.frameNb = PK.frameNb;
            PI.frameType = PK.frameType;
            PI.dataPriority = PK.prioNb;
        }
        else
        {
            lineStream >> PI.sendTime >> PI.frameNb >> PI.frameType >> PI.dataPriority >> PI.dataSize >> data;
        }
        if (lineStream.fail() || data.empty() || data == "-" || PI.dataPriority < 1)
            continue;
        pair<int, int> key(PI.frameNb, PI.dataPriority);
        if (heads.find(key) == heads.end())
            heads[key] = PI;
        units[key].push_back(data);
    }
    trace.close();

    vector<prioritiesInfo> levelsInfo;
    for (auto &h : heads)
    {
        prioritiesInfo PI = h.second;
        PI.level = packetDecoder(PI.dataPriority, units[h.first]);
        levelsInfo = priorityDecoder(IP, levelsInfo, PI);
    }
    return levelsInfo;
}
