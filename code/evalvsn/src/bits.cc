// bits.cc - bit strings: an integer written on a fixed number of bits and
// read back, and a bit string written as hexadecimal digits and read back.

#include "evalvsn.h"

string dec2bin(double dec, int bits)
{
    string bin;
    int r;

    bin.assign(bits, '0');

    for (int i = bits - 1; i >= 0; i--)
    {
        r = floor(fabs(dec) / 2.0);

        bin.replace(i, 1, to_string(((int)fabs(dec)) - (2 * r)));

        dec = r;
    }

    return bin;
}

double bin2dec(string bin, int bits)
{
    double dec = 0;

    for (int i = 0; i <= bits - 1; i++)
    {
        dec += atoi(bin.substr(i, 1).c_str()) * pow(2, bits - i - 1);
    }

    return dec;
}

prioritiesInfo hexEncoder(prioritiesInfo PI)
{
    map<string,string> bin2hex = {{"0000","0"},{"0001","1"},{"0010","2"},{"0011","3"},{"0100","4"},{"0101","5"},{"0110","6"},{"0111","7"},{"1000","8"},{"1001","9"},{"1010","A"},{"1011","B"},{"1100","C"},{"1101","D"},{"1110","E"},{"1111","F"}};
    string hex;
    
    for (int i = 0;i < ((int) PI.data.length());i += 4)
    {
        hex += bin2hex[PI.data.substr(i,4)];
    }
    
    PI.data = hex;
    
    return PI;
}

prioritiesInfo hexDecoder(prioritiesInfo PI)
{
    map<string,string> hex2bin = {{"0","0000"},{"1","0001"},{"2","0010"},{"3","0011"},{"4","0100"},{"5","0101"},{"6","0110"},{"7","0111"},{"8","1000"},{"9","1001"},{"A","1010"},{"B","1011"},{"C","1100"},{"D","1101"},{"E","1110"},{"F","1111"}};
    string bin;
    
    for (int i = 0;i < ((int) PI.data.length());i++)
    {
        bin += hex2bin[PI.data.substr(i,1)];
    }
    
    PI.data = bin;
    
    return PI;
}
