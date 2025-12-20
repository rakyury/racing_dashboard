#include "runtime.h"

#include <stdio.h>

int main(void) {
    Runtime rt_touchgfx;
    runtime_init(&rt_touchgfx);
    demo_touchgfx(&rt_touchgfx, 0);

    Runtime rt_lvgl;
    runtime_init(&rt_lvgl);
    demo_lvgl(&rt_lvgl, 0);

    return 0;
}

