import asyncio
import random


TIME = 0.0
MAX_TURN_IN_SEC_DEGREES = 3
MAX_BANK_DEGREES = 30
CURRENT_BANK_DEGREES = 0
MAX_SPEED = 350 * 1000 / 3600  # not used yet
# R_MIN = SPEED ** 2 / 9.81 / math.tan(math.radians(MAX_BANK_DEGREES))
# MAX_TIME_TURN = R_MIN / SPEED  # simplified
MAX_AILERON_COEFF = 1  # for simplified -1...1
CURRENT_AILERON_COEFF = 0  # -1...0 - left down, right up 0..1 - left up, right down, 0 - no

CURRENT_COURSE = 5
AUTOPILOT_TASK = None
AILERON_TASK = None


# TODO prowl?
async def autopilot_task(new_course: float):
    global CURRENT_COURSE
    global AUTOPILOT_TASK

    if AUTOPILOT_TASK is not None and not AUTOPILOT_TASK.cancelled():
        AUTOPILOT_TASK.cancel()
    AUTOPILOT_TASK = asyncio.current_task()

    if 359 < new_course < 0:
        print('ERROR: Incorrect Cource')
        return

    print(f'change current course from {CURRENT_COURSE} to {new_course}')
    while True:
        asyncio.ensure_future(set_aileron_degrees(new_course))
        await asyncio.sleep(0)


def get_course_diff(new_course: float):
    cource_diff = new_course - CURRENT_COURSE
    if cource_diff == 0:
        return

    if abs(cource_diff) > 180:
        if cource_diff > 0:
            cource_diff = cource_diff - 360
        else:
            cource_diff = 360 - cource_diff + CURRENT_COURSE

    return cource_diff


async def set_aileron_degrees(course: float):
    global CURRENT_AILERON_COEFF
    global AILERON_TASK
    global CURRENT_COURSE

    if AILERON_TASK is not None and not AILERON_TASK.cancelled():
        AILERON_TASK.cancel()
    AILERON_TASK = asyncio.current_task()

    if course == CURRENT_COURSE:
        CURRENT_AILERON_COEFF = 0
        return

    cource_diff = get_course_diff(course)
    turn_on = abs(cource_diff) / MAX_TURN_IN_SEC_DEGREES
    m = 1 if cource_diff > 1 else -1

    if turn_on >= 1:
        CURRENT_AILERON_COEFF = MAX_AILERON_COEFF * m
    elif turn_on:
        CURRENT_AILERON_COEFF = MAX_AILERON_COEFF * turn_on * m  # problem with unit
    await asyncio.sleep(0)


async def model_bank():
    global CURRENT_BANK_DEGREES
    print('RUN MODEL BANK')
    while True:
        # TODO smoothness factor, Speed ...
        new_bank_degrees = CURRENT_AILERON_COEFF * MAX_BANK_DEGREES
        aileron_diff = new_bank_degrees - CURRENT_BANK_DEGREES
        m = 1 if aileron_diff >= 0 else -1
        for i in range(int(abs(new_bank_degrees))):
            CURRENT_BANK_DEGREES += m
            aileron_diff -= 1 * m
            await asyncio.sleep(0.1)
        CURRENT_BANK_DEGREES += aileron_diff
        await asyncio.sleep(0.1 * abs(aileron_diff))


async def model_cource():
    global CURRENT_COURSE
    global CURRENT_BANK_DEGREES
    global MAX_TURN_IN_SEC_DEGREES
    print('RUN MODEL COURSE')
    while True:
        k = CURRENT_BANK_DEGREES / MAX_BANK_DEGREES
        CURRENT_COURSE += MAX_TURN_IN_SEC_DEGREES * k
        if CURRENT_COURSE < 0:
            CURRENT_COURSE += 360
        elif CURRENT_COURSE > 359:
            CURRENT_COURSE -= 360
        await asyncio.sleep(1)


async def print_data():
    while True:
        print(f'CURRENT COURSE: {CURRENT_COURSE:6.2f} | '
              f'CURRENT BANK: {CURRENT_BANK_DEGREES:6.2f} | '
              f'CURRENT AILERON {CURRENT_AILERON_COEFF:4.2f}')
        await asyncio.sleep(1.5)


async def main():
    asyncio.ensure_future(model_bank())
    asyncio.ensure_future(model_cource())
    asyncio.ensure_future(print_data())
    await asyncio.sleep(0)
    for i in range(4):
        new_course = round(random.uniform(0.0, 12.0), 2)
        # new_course = 8.222512943948026
        print(f'NEW TASK COURSE: {new_course}')
        asyncio.ensure_future(autopilot_task(new_course))
        await asyncio.sleep(random.randint(0, 15))


if __name__ == '__main__':
    run_app = asyncio.ensure_future(main())
    event_loop = asyncio.get_event_loop()
    event_loop.run_forever()
