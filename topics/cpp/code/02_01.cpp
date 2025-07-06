#include <iostream>
#include <cmath>
using namespace std;

int main(){
    // order of operations
    cout << (2 + 3 * 4) << endl;
    cout << (2 + 3) * 4 << endl;

    // divisions
    cout << endl;
    cout << 7 / 3 << endl;
    cout << float(7) / 3 << endl;
    cout << 7. / 3 << endl;
    cout << 6. / 3 << endl;

    // modulo & pow
    cout << endl;
    cout << 7 % 3 << endl;
    cout << pow(2, 10) << endl;
    cout << pow(2, 100) << endl;

    return 0;
}
