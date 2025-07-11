#include <iostream>
#include <iomanip>
using namespace std;

double squareroot(float a, int n_steps = 10) {
    int i;
    double x = a / 2;
    cout << fixed << setprecision(10);

    for (i = 0; i < n_steps; i++) {
        x = 0.5 * (x + a / x);
        cout << x << "\t" << "| err: " << x * x - a << endl;
    }

    return x;
}

int main() {
    double a; cin >> a;
    double x;
    x = squareroot(a);
    cout << "\noutput: " << x;
    return 0;
}
