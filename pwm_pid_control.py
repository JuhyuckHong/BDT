import time
from simple_pid import PID
import sensor_and_controller

def duty_transformation(input_value, min_value, max_value):
    # 입력 값이 최소와 최대 값 사이에 있는지 확인
    if not 0 <= input_value <= 100:
        raise ValueError("Input value should be between 0 and 100")
    
    # 변환 함수
    if min_value > max_value:
        # Forward flow일 때, 0~100까지를 45~10으로 변환
        min_value, max_value = max_value, min_value
        transformed_value = (1 - input_value / 100) * (max_value - min_value) + min_value

    else:
        # Reverse flow일 때, 0~100까지를 55~90으로 변환
        transformed_value = (input_value / 100) * (max_value - min_value) + min_value

    return round(transformed_value)

def get_duty(target, delay, average_time, control_limit, duty_min=0, duty_max=100, test=True):
    '''
    [2023-11-18]
    reversible fan 사용 시 pwm duty 
    10~45 까지 forward (가압) 10이 max, 45가 min
    55~90 까지 reverse (감압) 55가 min, 90이 max
    duty를 기반으로 pressure 제어 하는 코드를 실행하기 위해, duty 변환 함수를 사용해서 제어
    initial controlled duty = 0 → pwm-pressure PID control → duty result → function^-1(duty result) → real duty
    '''

    # 테스트 모드
    if test: 
        return (duty_max, True, target)
    # 현재 압력 값 측정 및 초기값 세팅
    current = abs(sensor_and_controller.pressure_read(0.1, test=test))
    duty = 0

    # 압력 수렴 조건
    convergence_time = 0
    pressure_threshold = target/10
    duration = 10
    # duty 수렴 조건
    window = []
    window_size = 50

    # 실패 조건
    failure_time = 0
    failure_threshold = 20

    # 종료 측정 조건
    final_measure_time = 5

    # PID 컨트롤러 생성
    pid = PID(1, 0, 0, setpoint=target)
    pid.auto_mode = True
    pid.output_limits = (-control_limit, control_limit)

    while True:
        # 제어 시작 시간
        time_start = time.time()
        print(time_start)
        # PID 계산
        control = pid(current)
        # duty 업데이트 및 상하한 설정
        duty += control
        duty = round(duty)
        duty = max(0, min(100, duty))
        # PID 제어용 duty에서 실제 duty값으로 변경
        duty_real = duty_transformation(duty, duty_min, duty_max)
        # duty 값 적용
        sensor_and_controller.duty_set(duty_real, test=False)
        # 압력 변화 대기
        time.sleep(delay)
        # 압력 값 측정
        current = abs(sensor_and_controller.pressure_read(average_time, test=test))
        # duty의 이동 평균 계산
        window.append(duty)
        if len(window) > window_size:
            window = window[1:]

        duty_avg = sum(window)/len(window)

        # 제어 종료 시간
        time_diff = time.time() - time_start
        print(time_diff)
        # 압력 오차
        error_pressure = abs(target - current)
        # duty 오차 # 사용하지 않음
        error_duty = abs(duty_avg - duty)
        print(f"current pressure: {current:.2f}, error: {error_pressure:.2f}, target: {target}")

        if error_pressure < pressure_threshold: # and error_duty < max(2, duty/10):
            convergence_time += time_diff
            print(f"Converging... ({convergence_time}s)")
        else:
            convergence_time = 0
            print(f"Converging failed")

        if convergence_time >= duration:
            current = abs(sensor_and_controller.pressure_read(final_measure_time, test=test))
            print(f"Control finished with pressure({current}) for target({target})")
            # 실제 duty값으로 변환 후 반환
            duty_real = duty_transformation(duty, duty_min, duty_max)
            return (duty_real, True, current)

        # duty 100으로 설정해도 목표 압력에 도달하지 못하는 경우
        if duty == 100 and error_pressure > failure_threshold:
            print(f"With duty=100, cannot reach the target pressure({target}), current pressure({current})")
            failure_time += time_diff
            print(f"failure time: {failure_time}, duration: {duration}")
        # duty 0으로 설정해도 목표 압력 값을 초과하는 경우
        elif duty == 0 and error_pressure > failure_threshold:
            print(f"At duty=0, current pressure({current}) exceed the target pressure ({target})")
            failure_time += time_diff
            print(f"failure time: {failure_time}, duration: {duration}")
        else:
            failure_time = 0

        if failure_time >= duration:
            current = abs(sensor_and_controller.pressure_read(final_measure_time, test=test))
            print(f"Control failed.")
            # 실제 duty값으로 변환 후 반환
            duty_real = duty_transformation(duty, duty_min, duty_max)
            return (duty_real, False, current)
