#include "evalvsn.h"

// packet.cc - the packets of a priority level. Each packet starts on a code
// word and carries, in its first two bytes, the index of its first
// coefficient in the level: it decodes alone, and a lost packet costs the
// coefficients it carries and no others, as a slice of H.264 or a restart
// interval of JPEG.

static const int kPacketHeaderBits = 16;

// The code words that travel together: one (run, value) pair of the
// run-length coding, which covers `coefs` coefficients of the level.
struct CodeGroup
{
    int firstCodeWord;
    int codeWords;
    long coefs;
};

vector<string> packetEncoder(inputParameters IP, prioritiesInfo PI, Mat_<double> elems)
{
    vector<CodeGroup> groups;
    int cw = 0;
    for (int p = 0; p + 1 < elems.cols; p += 2)
    {
        long run = (long)elems.at<double>(p);
        groups.push_back({cw, 2, run});
        cw += 2;
    }

    int codeWords = groups.empty() ? 0 : groups.back().firstCodeWord + groups.back().codeWords;
    if (codeWords != (int)PI.levelSize.size())
    {
        cerr << "packetEncoder: " << codeWords << " code words grouped, " << PI.levelSize.size()
             << " coded (frame " << PI.frameNb << ", level " << PI.dataPriority << ")\n";
        exit(EXIT_FAILURE);
    }

    const long budget = (long)IP.mpl * 8 - kPacketHeaderBits;
    vector<string> units;
    long coef = 0;
    size_t g = 0;
    while (g < groups.size())
    {
        long start = coef;
        string bits;
        while (g < groups.size())
        {
            int first = groups[g].firstCodeWord;
            int last = first + groups[g].codeWords - 1;
            int a = PI.levelOffset[first];
            int b = PI.levelOffset[last] + PI.levelSize[last];
            if (!bits.empty() && (long)bits.size() + (b - a) > budget)
                break;
            if (bits.empty() && (b - a) > budget)
            {
                cerr << "packetEncoder: a code group of " << (b - a) << " bits exceeds the packet\n";
                exit(EXIT_FAILURE);
            }
            bits += PI.data.substr(a, b - a);
            coef += groups[g].coefs;
            g++;
        }
        if (start > 65535)
        {
            cerr << "packetEncoder: coefficient index " << start << " needs more than two bytes\n";
            exit(EXIT_FAILURE);
        }
        prioritiesInfo unit;
        // The padding is of ones: a run of ones never completes an
        // Exp-Golomb code word (a zero ends its prefix).
        unit.data = dec2bin(start, kPacketHeaderBits) + bits;
        unit.data.append((8 - unit.data.size() % 8) % 8, '1');
        units.push_back(hexEncoder(unit).data);
    }
    return units;
}

// The coefficients of a level rebuilt from the packets that arrived; the
// coefficients of the lost packets stay at zero.
Mat_<double> packetDecoder(int dataPriority, const vector<string> &units)
{
    vector<double> coefs;
    for (const string &u : units)
    {
        prioritiesInfo P;
        P.dataPriority = dataPriority;
        P.data = u;
        P = hexDecoder(P);
        if ((int)P.data.size() < kPacketHeaderBits)
            continue;
        long idx = (long)bin2dec(P.data.substr(0, kPacketHeaderBits), kPacketHeaderBits);
        P.data = P.data.substr(kPacketHeaderBits);
        P = expGolombDecoder(P);
        for (int p = 0; p + 1 < P.level.cols; p += 2)
        {
            long run = (long)P.level.at<double>(p);
            double value = P.level.at<double>(p + 1);
            for (long k = 0; k < run; k++, idx++)
            {
                if (idx >= (long)coefs.size())
                    coefs.resize(idx + 1, 0.0);
                coefs[idx] = value;
            }
        }
    }
    Mat_<double> level(1, (int)coefs.size());
    for (int k = 0; k < (int)coefs.size(); k++)
        level.at<double>(k) = coefs[k];
    return level;
}
