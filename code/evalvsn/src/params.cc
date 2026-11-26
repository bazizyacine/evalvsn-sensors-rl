// params.cc - one line of the encoder file:
//   simId MMPEG FPS Threshold gopCoef qualityCoef priorityNb CLA8 RLE1 EG
// The last three fields name the coding the codec implements, the classical
// 8x8 DCT, run-length coding of every level and Exp-Golomb code words; a line
// that asks for another is refused.

#include "evalvsn.h"

// A simId names a directory: no path separator or shell-hostile character,
// not "." or "..", not ending in a dot or a space.
bool isValidSimId(const string &simId)
{
    return regex_match(simId, regex(R"(^(?!\.{1,2}$)[^\\/:*?"<>|]*[^\\/:*?"<>|\. ]$)"));
}

bool isValidInt(const string &s)
{
    return regex_match(s, regex("^[0-9]+$"));
}

bool isValidDouble(const string &s)
{
    return regex_match(s, regex("^[0-9]*\\.?[0-9]+$"));
}

bool isValidPriorityNb(const string &pn)
{
    int p = stoi(pn);
    return p >= 1 && p <= 13;
}

bool getIP(inputParameters &IP, const string &line, string &errParam)
{
    stringstream lineStream(line);
    string FPSStr, thresholdStr, gopCoefStr, qualityCoefStr, priorityNbStr, dctStr, rleStr, binStr;

    lineStream >> IP.simId >> IP.encoder >> FPSStr >> thresholdStr >> gopCoefStr >> qualityCoefStr >> priorityNbStr >> dctStr >> rleStr >> binStr;

    if (!isValidSimId(IP.simId))
    {
        errParam = "simId";
        return false;
    }
    if (IP.encoder != "MMPEG")
    {
        errParam = "Encoder (MMPEG)";
        return false;
    }
    if (!isValidDouble(FPSStr))
    {
        errParam = "FPS";
        return false;
    }
    if (!isValidInt(thresholdStr))
    {
        errParam = "Threshold";
        return false;
    }
    if (!isValidDouble(gopCoefStr))
    {
        errParam = "gopCoef";
        return false;
    }
    if (!isValidDouble(qualityCoefStr))
    {
        errParam = "qualityCoef";
        return false;
    }
    if (!isValidInt(priorityNbStr) || !isValidPriorityNb(priorityNbStr))
    {
        errParam = "priorityNb";
        return false;
    }
    if (dctStr != "CLA8")
    {
        errParam = "DCTzoneSize (CLA8)";
        return false;
    }
    if (rleStr != "RLE1")
    {
        errParam = "rleLevel (RLE1)";
        return false;
    }
    if (binStr != "EG")
    {
        errParam = "binLevel (EG)";
        return false;
    }

    IP.FPS = stod(FPSStr);
    IP.threshold = stoi(thresholdStr);
    IP.gopCoef = stod(gopCoefStr);
    IP.qualityCoef = stod(qualityCoefStr);
    IP.priorityNb = stoi(priorityNbStr);

    return true;
}
