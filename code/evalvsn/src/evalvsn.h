// evalvsn.h - the data structures and functions of the EvalVSN codec: a video
// cut into frames of type M (coded alone) or D (coded against the last M
// frame), each 8x8 block transformed by the classical DCT, quantised, read in
// zigzag order and split into 13 priority levels, every level run-length and
// Exp-Golomb coded and cut into packets that decode alone.

#include <opencv2/opencv.hpp>
#include <opencv2/highgui.hpp>
#include <fstream>
#include <sys/stat.h>
#include <set>
#include <regex>
#include <filesystem>

using namespace std;
using namespace cv;

struct inputParameters
{
    string simId;
    string encoder;
    string imageResolution;
    int imagesNb;
    int videoDuration;
    double FPS;
    int threshold;
    double gopCoef;
    double qualityCoef;
    int priorityNb;
    string payloadFormat;
    string rcvFile;
    // The packet payload in bytes, header included (-mpl, 74 by default):
    // the encoder cuts each priority level into packets of this size.
    int mpl = 74;
};

struct prioritiesInfo
{
    double sendTime;
    int frameNb;
    string frameType;
    int dataPriority;
    int dataSize;
    string data;
    int blockNb;
    Mat_<double> level;
    vector<int> levelSize;
    vector<int> levelOffset;
};

struct framesInfo
{
    int frameNb;
    string frameType;
    int frameSize;
    double refPSNR = 0;
    double refSSIM = 0;
    double compRatio = 0;
};

struct packetsInfo
{
    double sTime;
    int seqNb;
    int pSize;
    int frameNb;
    string frameType;
    int prioNb;
    int offset;
};

struct metricsInfo
{
    int frameNb;
    double psnr = 0;
    double ssim = 0;
    double pktLoss = 0;
    double pktLossM = 0;
    double pktLossD = 0;
    Mat_<double> pktlossPriority = Mat::zeros(2, 13, CV_64F);
};

// params.cc: one line of the encoder file
bool isValidSimId(const string &simId);
bool isValidInt(const string &s);
bool isValidDouble(const string &s);
bool isValidPriorityNb(const string &pn);
bool getIP(inputParameters &IP, const string &line, string &errParam);

// evalvsn.cc
void mkDir(string pathName);

// video.cc: the video, its frames and their type
void avi2png(inputParameters IP, string videoFile, string outputDirectory);
int videoEncoder(inputParameters IP, string videoFile, string outputDirectory);
int videoDecoder(inputParameters IP, string videoFile, string outputDirectory);
void png2avi(inputParameters IP, string videoFile, string outputDirectory);

// frame.cc, dct.cc, quantification.cc, zigzag.cc, priority.cc: the blocks
vector<prioritiesInfo> frameEncoder(inputParameters IP, Mat_<double> encodedFrame, prioritiesInfo PI);
Mat_<double> frameDecoder(inputParameters IP, Mat_<double> decodedFrame);
Mat_<double> dctEncoder(Mat_<double> block);
Mat_<double> dctDecoder(Mat_<double> blockDCT);
Mat_<double> quantificationEncoder(inputParameters IP, Mat_<double> blockDCT);
Mat_<double> quantificationDecoder(inputParameters IP, Mat_<double> blockQTF);
Mat_<double> zigzagEncoder(Mat_<double> blockQTF);
Mat_<double> zigzagDecoder(Mat_<double> blockZigZag, int vmax, int hmax);
vector<prioritiesInfo> priorityEncoder(inputParameters IP, Mat_<double> blockZigZag, vector<prioritiesInfo> vecPI, prioritiesInfo PI);
vector<prioritiesInfo> priorityDecoder(inputParameters IP, vector<prioritiesInfo> &levelsInfo, prioritiesInfo PI);  // by reference: the vector grows to 60 000 entries, copying it per level was quadratic

// rle.cc, golomb.cc, bits.cc: the code words
prioritiesInfo rleEncoder(prioritiesInfo PI);
prioritiesInfo expGolombEncoder(prioritiesInfo PI);
prioritiesInfo expGolombDecoder(prioritiesInfo PI);
double negativeEncoder(double dec);
double negativeDecoder(double ne);
string unaryEncoder(double ne);
double unaryDecoder(string ue);
double getGroupID(double ne);
string dec2bin(double dec, int bits);
double bin2dec(string bin, int bits);
prioritiesInfo hexEncoder(prioritiesInfo PI);
prioritiesInfo hexDecoder(prioritiesInfo PI);

// packet.cc, trace.cc: the packets and the traces
vector<string> packetEncoder(inputParameters IP, prioritiesInfo PI, Mat_<double> elems);
Mat_<double> packetDecoder(int dataPriority, const vector<string> &units);
void traceEncoder(inputParameters IP, vector<prioritiesInfo> vecPI, vector<framesInfo> vecFI, string priorityName, string frameName);
vector<prioritiesInfo> traceDecoder(inputParameters IP, string unitsName, bool received);

// evaluate.cc: the quality measures
int traceEvaluate(inputParameters IP, string videoFile, string outputDirectory);
double psnrEvaluate(Mat_<double> capturedFrame, Mat_<double> decodedFrame);
double ssimEvaluate(Mat_<double> capturedFrame, Mat_<double> decodedFrame);
double ratioEvaluate(int capturedFrameSize, int decodedFrameSize);
double mseEvaluate(Mat_<double> currentImage, Mat_<double> previousImage);
int frameZerosEvaluate(Mat_<double> frame);
int levelZerosEvaluate(Mat_<double> level);
