#include <iostream>
using namespace std;

int main(){
    cout << (5 == 10) << endl;
    cout << (10 > 5) << endl;
    cout << ((5 >= 1) && (5 <= 10)) << endl;
    cout << ((5 >= 1) || (1 / 0)) << endl;
    return 0;
}
