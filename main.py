import asyncio
import math


# R_MIN = SPEED ** 2 / 9.81 / math.tan(math.radians(MAX_BANK_DEGREES))
# T_MIN = 0.64 * R_MIN / 9.81 / math.tan(math.radians(MAX_BANK_DEGREES))
# MAX_TIME_TURN = R_MIN / SPEED  # simplified
# MAX_AILERON_COEFF = 1  # for simplified -1...1
MAX_TURN_IN_SEC_DEGREES = 3
MAX_BANK_IN_SEC_DEGREES = 10

AILERON_VALUE_DEGREES = 0

AILERON_TIME_ON_ONE_DEGREES = 0.2

MAX_BANK_DEGREES = 30  # -30...30
MAX_AILERON_DEGREES = 30  # -30...30

CURRENT_AILERON_DEGREES = 0  # simplify -30...0 - left down, right up 0..30 - left up, right down
CURRENT_BANK_DEGREES = 27
CURRENT_COURSE = 354.1999999999999
SPEED = 350 * 1000 / 3600  # m/s

AUTOPILOT_TASK = None
AILERON_TASK = None


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
        await asyncio.sleep(0.01)


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
    global AILERON_VALUE_DEGREES
    global AILERON_TASK

    if AILERON_TASK is not None and not AILERON_TASK.cancelled():
        AILERON_TASK.cancel()
    AILERON_TASK = asyncio.current_task()

    if abs(CURRENT_BANK_DEGREES) > MAX_BANK_DEGREES:
        m = 1 if CURRENT_AILERON_DEGREES > 0 else -1
        AILERON_VALUE_DEGREES = MAX_AILERON_DEGREES * m
        return

    course_diff = get_course_diff(course)
    turn_time = calculate_turn_time(
        turning_angle=abs(course_diff),
        speed=SPEED,
        bank_degrees=CURRENT_BANK_DEGREES,
    )

    if course_diff == 0:
        AILERON_VALUE_DEGREES = 0
        return

    m = 1 if course_diff > 1 else -1

    AILERON_VALUE_DEGREES = turn_time / MAX_TURN_IN_SEC_DEGREES * m
    if abs(AILERON_VALUE_DEGREES) > MAX_AILERON_DEGREES:
        AILERON_VALUE_DEGREES = MAX_AILERON_DEGREES * m

    await asyncio.sleep(0)


async def model_aileron():
    global CURRENT_AILERON_DEGREES
    print('RUN MODEL AILERON')
    while True:
        aileron_diff = -(CURRENT_AILERON_DEGREES - AILERON_VALUE_DEGREES)
        m = 1 if aileron_diff >= 0 else -1
        for i in range(int(abs(aileron_diff))):
            CURRENT_AILERON_DEGREES += m
            await asyncio.sleep(AILERON_TIME_ON_ONE_DEGREES)
        aileron_diff = (abs(aileron_diff) - abs(int(aileron_diff))) * m
        CURRENT_AILERON_DEGREES += aileron_diff
        await asyncio.sleep(abs(aileron_diff) / AILERON_TIME_ON_ONE_DEGREES)


async def model_bank():
    global CURRENT_BANK_DEGREES
    print('RUN MODEL BANK')
    while True:
        change_on = (CURRENT_AILERON_DEGREES / MAX_AILERON_DEGREES)
        if change_on == 0:
            await asyncio.sleep(0.1)
            continue
        m = 1 if change_on > 0 else -1
        for i in range(abs(int(change_on))):
            CURRENT_BANK_DEGREES += MAX_BANK_IN_SEC_DEGREES * m
            await asyncio.sleep(1)
        change_on = (abs(change_on) - abs(int(change_on))) * m
        CURRENT_BANK_DEGREES += change_on
        await asyncio.sleep(abs(change_on))


async def model_course():
    global CURRENT_COURSE
    print('RUN MODEL COURSE')
    while True:
        k = CURRENT_BANK_DEGREES / MAX_BANK_DEGREES
        CURRENT_COURSE += MAX_TURN_IN_SEC_DEGREES * k
        if CURRENT_COURSE < 0:
            CURRENT_COURSE += 360
        elif CURRENT_COURSE > 359:
            CURRENT_COURSE -= 360
        await asyncio.sleep(abs(k))


def calculate_turn_time(turning_angle: float, speed: float, bank_degrees: float):
    return (turning_angle / 360) * 0.64 * (speed / (9.81 * math.tan(math.radians(bank_degrees))))


async def print_data():
    while True:
        print(f'CURRENT COURSE: {CURRENT_COURSE:6.2f} | '
              f'CURRENT BANK: {CURRENT_BANK_DEGREES:6.2f} | '
              f'CURRENT AILERON: {CURRENT_AILERON_DEGREES:4.2f}')
        await asyncio.sleep(1.5)


async def main():
    asyncio.ensure_future(model_bank())
    asyncio.ensure_future(model_course())
    asyncio.ensure_future(model_aileron())
    asyncio.ensure_future(print_data())
    await asyncio.sleep(0)
    for i in range(1):
        # new_course = round(random.uniform(0.0, 359), 2)
        new_course = 350
        print(f'NEW TASK COURSE: {new_course}')
        asyncio.ensure_future(autopilot_task(new_course))
        # await asyncio.sleep(random.randint(0, 15))


if __name__ == '__main__':
    run_app = asyncio.ensure_future(main())
    event_loop = asyncio.get_event_loop()
    event_loop.run_forever()
