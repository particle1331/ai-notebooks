#include <iostream>
using namespace std;

int main(){
    string resp;
    cout << "\nEver heard of rubber duck debugging?" << endl;
    cin  >> resp;
    if ((resp[0] == 'Y') || (resp[0] == 'y')){
        cout << "cool B)" << endl;
    }
    else {
        cout << "Here you go." << endl;
        cout << "                __     " << endl;
        cout << "              <(o )___-" << endl;
        cout << "               ( .__> /" << endl;
        cout << "                `----' " << endl;
    }

    return 0;
}
