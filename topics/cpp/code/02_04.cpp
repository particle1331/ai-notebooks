#include <iostream>
using namespace std;

//  Demonstrates how to use variables in C++
//  moreover, we assign an integer to a boolean variable,
//  showing the static typing of C++.
int main(){

    int theSum = 4;
    cout << theSum << endl;

    theSum = theSum + 1;
    cout << theSum << endl;

    bool theBool = true;
    cout << theBool << endl;

    theBool = 4;
    cout << theBool << endl;

    return 0;
}
