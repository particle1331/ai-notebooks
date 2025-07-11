#include <iostream>
using namespace std;

double newton_step(double x, float a) {
    return 0.5 * (x + a / x);
}

float error(double x, float a) {
    return x * x - a;
}

int main() {
    int i;
    float eps = 1e-7;
    float a; cin >> a;
    float x = a / 2;        // Initial point

    for (i = 0; i < 10; i++) {
        x = newton_step(x, a);
        cout << x << "\t" << "| error: " << error(x, a) << endl;
    }

    return 0;
}
