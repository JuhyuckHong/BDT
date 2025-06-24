# -*- conding: utf-8 -*-
# 작업 디렉토리 설정
import os
path_script = os.path.abspath(__file__)
dir_script = os.path.dirname(path_script)
os.chdir(dir_script)
import sys
import json
import time
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout,
                             QPushButton, QGridLayout, QCheckBox, QMainWindow,
                             QMessageBox, QComboBox, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer, QPointF, Qt, QThread, pyqtSignal, QCoreApplication
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap
import ACH_calculator
import graph_plotter
import reporting
import pwm_pid_control
import sensor_and_controller
import platform
current_os = platform.system()
if current_os == "Windows":
    test_mode = True
else:
    test_mode = False

class InputInitalValues(QWidget):
    def __init__(self):
        super().__init__()
        # 창 크기 고정
        # 전체 화면 모드로 설정
        #self.showFullScreen()     
        # 사이즈 조정
        #self.resize(800, 480)
        # 레이아웃 설정
        layout = QGridLayout()
        self.setLayout(layout)

        # 스타일 시트 적용
        self.setStyleSheet('''
            QWidget {
                background-color: #F5F5F5;
            }
            QLabel {
                font-family: Arial;
                font-size: 12px;
                color: #333333;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
            }
            QPushButton {
                padding: 5px;
                background-color: #E0E0E0;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QLineEdit::placeholder {
            color: (0.7, 0.7, 0.7, 0.5);
            }
        ''')

        # 입력 필드와 레이블 생성
        # (표시되는 레이블, 저장되는 key, placeholder)
        labels = [
            ("시험 목적", "purpose", "기밀 시험"),
            ("위치", "location", "서울시 송파구 풍납동 497"),
            ("테스트 방식", "method", "method A / method B"),
            ("의뢰자", "requester", "홍길동, 010-0000-0000"),
            ("설계사", "designer", "OO건축사사무소"),
            ("시험자", "tester", "김철수 (주)기밀시험"),
            ("시공사(시공자)", "builder", "OO건축"),
            ("실내 체적 (㎥)", "interior volume", "(필수) 424.21 와 같이 숫자만 작성 가능합니다."),
            ("연면적 (㎡)", "floor area", "92.4"),
            ("구조", "structure", "경량목구조")
        ]
        self.input_fields = {}
        for row, (label_text, label_key, plcae_holder) in enumerate(labels):
            label = QLabel(label_text)
            input_field = QLineEdit()
            # 플레이스홀더
            input_field.setPlaceholderText(plcae_holder)
            # 왼쪽 열에 라벨 추가
            layout.addWidget(label, row, 0)
            # 오른쪽 열에 입력 필드 추가
            layout.addWidget(input_field, row, 1)
            # 데이터 저장
            self.input_fields[label_key] = input_field

        next_row = row + 1

        # 팬 설정 드롭다운
        fan_count_label = QLabel("팬 개수")
        self.fan_count_cb = QComboBox()
        self.fan_count_cb.addItems(["1", "2"])
        self.fan_count_cb.setCurrentText("2")
        layout.addWidget(fan_count_label, next_row, 0)
        layout.addWidget(self.fan_count_cb, next_row, 1)
        next_row += 1

        fan_cover1_label = QLabel("팬1 커버")
        self.fan_cover1_cb = QComboBox()
        self.fan_cover1_cb.addItems(["none", "low", "high"])
        layout.addWidget(fan_cover1_label, next_row, 0)
        layout.addWidget(self.fan_cover1_cb, next_row, 1)
        next_row += 1

        fan_cover2_label = QLabel("팬2 커버")
        self.fan_cover2_cb = QComboBox()
        self.fan_cover2_cb.addItems(["none", "low", "high"])
        layout.addWidget(fan_cover2_label, next_row, 0)
        layout.addWidget(self.fan_cover2_cb, next_row, 1)
        self.fan_cover2_label = fan_cover2_label
        self.fan_cover2_cb.hide()
        self.fan_cover2_label.hide()
        next_row += 1

        self.fan_count_cb.currentIndexChanged.connect(self.update_fan_cover_visibility)

        # 초기 팬 개수 설정에 맞춰 두 번째 팬 커버 가시성 업데이트
        self.update_fan_cover_visibility()

        # 체크박스 데이터
        self.checkbox_states = {}

        # 체크 박스 생성
        checkbox1 = QCheckBox("감압 실험")
        checkbox1.setObjectName("depressurization")
        checkbox1.stateChanged.connect(self.save_checkbox_state)
        layout.addWidget(checkbox1, next_row, 0)

        checkbox2 = QCheckBox("가압 실험")
        checkbox2.setObjectName("pressurization")
        checkbox2.stateChanged.connect(self.save_checkbox_state)
        layout.addWidget(checkbox2, next_row + 1, 0)

        # 저장 버튼 생성
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button, next_row + 1, 1)

    def save_checkbox_state(self):
        sender = self.sender()
        checkbox_text = sender.objectName()
        checkbox_state = sender.isChecked()

        self.checkbox_states[checkbox_text] = checkbox_state

    def update_fan_cover_visibility(self):
        """Show or hide second fan cover option based on fan count."""
        if int(self.fan_count_cb.currentText()) >= 2:
            self.fan_cover2_cb.show()
            self.fan_cover2_label.show()
        else:
            self.fan_cover2_cb.hide()
            self.fan_cover2_label.hide()

    def save_data(self):
        # 필수 값인 'interior volume' 값이 비어있는지 확인
        interior_volume = self.input_fields["interior volume"].text()
        if not interior_volume.strip():
            # 경고 메시지 표시
            QMessageBox.warning(self, "입력 오류", "'실내 체적 (㎥)'는 필수 입력 사항입니다.")
            return
        
        # 감압 또는 가압 중 적어도 하나가 선택되었는지 확인
        is_checked = self.checkbox_states.get("depressurization", False) or self.checkbox_states.get("pressurization", False)
        if not is_checked:
            QMessageBox.warning(self, "선택 오류", "'감압 실험' 또는 '가압 실험' 중 하나는 선택해야 합니다.")
            return

        data = {}
        # 입력값을 JSON 파일로 저장
        for key, input_field in self.input_fields.items():
            value = input_field.text()
            data[key] = value
        # 팬 선택 및 커버 정보 저장
        data["fan_count"] = int(self.fan_count_cb.currentText())
        data["fan_cover1"] = self.fan_cover1_cb.currentText()
        if data["fan_count"] >= 2:
            data["fan_cover2"] = self.fan_cover2_cb.currentText()
        # 체크박스 데이터 저장
        for key, checkbox in self.checkbox_states.items():
            data[key] = checkbox
        # json으로 저장 (다음 프로세스용)
        with open("conditions.json", "w") as file:
            json.dump(data, file, indent=4)
        # json으로 저장 (백업용)
        now = datetime.now().strftime("%y%m%d-%H%M%S")
        with open(f"./conditions/conditions_{now}.json", "w") as file:
            json.dump(data, file, indent=4)
        # 종료
        self.close()


class LivePressureData(QMainWindow):
    def __init__(self, initial_message="실시간 압력 측정"):
        super(LivePressureData, self).__init__()

        # 초기 시리즈와 차트 설정
        self.series = QLineSeries()
        self.chart = QChart()
        self.chart.legend().setVisible(False)  # Hide the legend
        self.chart.addSeries(self.series)

        # x, y 축 생성
        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()
        
        # 축 범위 설정
        self.axis_x.setRange(0, 100)
        self.axis_y.setRange(0, 100)

        # 축 레이블 설정
        self.axis_x.setTitleText("Time (s)")
        self.axis_y.setTitleText("Pressure (Pa)")

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        # 메세지 레이블
        self.message_label = QLabel(initial_message)

        # 측정 시작 버튼
        self.stop_button = QPushButton("측정 시작")

        # 차트를 메인 위젯으로 설정
        self.chart_view = QChartView(self.chart)

        # 메인 위젯 설정
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.addWidget(self.message_label)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.chart_view)
        self.setCentralWidget(main_widget)

        # 초기 데이터 (x는 시간, y는 랜덤값)
        self.data = [QPointF(i, sensor_and_controller.pressure_read(test=test_mode)) for i in range(10)]
        self.series.replace(self.data)

        # 타이머 설정 (1초마다 update_chart 호출)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(100)

        # 측정 종료 버튼 클릭 이벤트 연결
        self.stop_button.clicked.connect(self.timer.stop)
        self.stop_button.clicked.connect(self.close)

    def update_chart(self):
        # 새로운 측정값을 데이터에 추가
        new = sensor_and_controller.pressure_read(test=test_mode)
        self.data.append(QPointF(self.data[-1].x() + 1, new))
        # 데이터가 100개를 초과하면 가장 오래된 데이터를 제거
        if len(self.data) > 100:
            self.data.pop(0)
            self.axis_x.setRange(self.data[0].x(), self.data[-1].x())

        # 시리즈와 축을 업데이트
        self.series.replace(self.data)


class SimpleMessageAutoDisappear(QMainWindow):
    def __init__(self, initial_message="warning", time_to_close=10):
        super(SimpleMessageAutoDisappear, self).__init__()
        # 창의 제목을 초기 메시지로 설정
        self.setWindowTitle(initial_message)
        # QLabel 위젯을 생성하여 초기 메시지 표시
        self.label = QLabel(initial_message, self)
        # QLabel을 창의 중앙 위젯으로 설정
        self.setCentralWidget(self.label)
        # 글자 중간 정렬
        self.label.setAlignment(Qt.AlignCenter)
        # 남은 닫히기까지의 시간을 10으로 초기화
        self.time_to_close = time_to_close
        # 메시지 업데이트 메서드 호출
        self.update_message()

    def update_message(self):
        if self.time_to_close >= 0:
            message = f"{self.windowTitle()}\n{self.time_to_close}초 후에 창이 닫힙니다."
            self.label.setText(message)
            self.time_to_close -= 1
            # 1초 후에 다시 메시지 업데이트
            QTimer.singleShot(1000, self.update_message)
        else:
            self.close()


class SimpleMessage(QMainWindow):
    def __init__(self, initial_message="warning"):
        super(SimpleMessage, self).__init__()
        # 창의 제목 설정
        self.setWindowTitle(initial_message)
        # QLabel 위젯 생성
        self.label = QLabel(initial_message, self)
        # 글자 중간 정렬
        self.label.setAlignment(Qt.AlignCenter)
        # QLabel을 창의 중앙 위젯으로 설정
        self.setCentralWidget(self.label)


class ResultImageWindow(QWidget):
    def __init__(self, image_path, size_w, size_h):
        super().__init__()
        self.setWindowTitle('시험 결과 그래프')
        
        # 이미지를 QLabel에 표시하기 위한 QLabel 위젯 생성
        self.label = QLabel(self)
        # 이미지가 창에 맞게 리사이즈되도록 설정
        self.label.setScaledContents(True)
        
        # 이미지 파일을 QPixmap으로 로드
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(size_w, size_h, Qt.KeepAspectRatio)
        
        # QLabel에 QPixmap 설정
        self.label.setPixmap(pixmap)


class ResultTableWindow(QWidget):
    def __init__(self, test_data):
        super().__init__()
        self.setWindowTitle('Blower Door Test Report')

        # 테이블 위젯 설정
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(14)  # 필요한 행의 수
        self.tableWidget.setColumnCount(6)  # 필요한 열의 수
        self.tableWidget.setHorizontalHeaderLabels(['', '감압', '오차', '가압', '오차', '단위'])
        
        # 테이블 데이터 채우기
        self.populate_table(test_data)

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.tableWidget)
        self.setLayout(layout)

    def populate_table(self, data):
        # 시험 정보 섹션
        test_info_labels = ['시험 기간', '위치', '의뢰자', '시험자', '실내 체적', '연면적', '시험 목적', '테스트 방법', '설계사', '시공사', '구조']
        for i, label in enumerate(test_info_labels):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(label))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(data.get(label, '-')))

        # 시험 결과 섹션
        test_result_labels = ['시험 기준', 'Q50', 'ACH50', 'AL50', '누기 계수, C', '기류 지수, n', '결정 계수, r^2']
        for i, label in enumerate(test_result_labels, start=7):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(label))
            if label == '시험 기준':
                self.tableWidget.setItem(i, 1, QTableWidgetItem('KS-L-ISO-9972'))
            else:
                self.tableWidget.setItem(i, 1, QTableWidgetItem(str(data.get(label, '-'))))
                self.tableWidget.setItem(i, 2, QTableWidgetItem(str(data.get(label + ' 오차', '-'))))

        # 단위 설정
        self.tableWidget.setItem(9, 5, QTableWidgetItem('㎥/s'))
        self.tableWidget.setItem(10, 5, QTableWidgetItem('1/h'))
        self.tableWidget.setItem(11, 5, QTableWidgetItem('㎡'))
        self.tableWidget.setItem(12, 5, QTableWidgetItem('㎥/(h·Pa^n)'))
        self.tableWidget.setItem(13, 5, QTableWidgetItem('-'))


class BackgroundTask(QThread):
    finished = pyqtSignal()  # 작업 완료 시그널

    def __init__(self, task_type):
        super().__init__()
        self.task_type = task_type
        self.result = 0 # Initialize the result attribute

    def run(self):
        if self.task_type == "depressurization":
            self.blower_door_test(self.task_type)
        elif self.task_type == "pressurization":
            self.blower_door_test(self.task_type)
        elif self.task_type == "calculation":
            self.calculation()
        elif self.task_type == "graph_plotting":
            self.graph_plotting()
        elif self.task_type == "reporting":
            self.reporting()

        self.finished.emit()  # 작업 완료 시그널 발생

    @staticmethod
    def measuring_pressure(total_duration, local_duration):
        # 압력 측정
        pressure = []
        # 측정 시간
        pressure_size = total_duration
        while pressure_size:
            measuring_duration = local_duration
            pressure.append(sensor_and_controller.
                            pressure_read(average_time=
                                          measuring_duration,
                                          test=test_mode))
            pressure_size -= measuring_duration
        # 측정 평균값 저장
        return sum(pressure)/len(pressure)

    def blower_door_test(self, test):

        # 측정 모드에 따른 변수 설정
        # 사용중인 팬의 설정값
        stop_duty = 0
        min_duty, max_duty = 20, 100
        initial_duty = min_duty

        # 측정
        measuring = {}
        measuring["measured_value"] = []
        # 온습도, 대기압
        measuring["temperature"] = 20
        measuring["relative_humidity"] = 50
        measuring["atmospheric_pressure"] = 101325
        # 테스트 기록
        measuring["test"] = test
        # 시험 시작 시간
        time_start = datetime.now().strftime("%H:%M:%S")

        # 시작 0 기류 압력 측정 # 현재 버전에서는 생략
        # measuring["initial_zero_pressure"] = self.measuring_pressure(10, 1)

        # 시험 시작 전 PWM duty를 0으로 설정
        sensor_and_controller.duty_set(stop_duty, test=test_mode)

        # 시험 시작
        success = False
        # 70Pa PWM duty 값 추출
        (duty, success, pressure) = pwm_pid_control.get_duty(target=70,
                                                             delay=5,
                                                             average_time=0.5,
                                                             control_limit=10,
                                                             duty_min=min_duty,
                                                             duty_max=max_duty,
                                                             test=test_mode)
        print(f"max duty: {duty}, control: {success}, pressure at duty: {pressure}")

        # 70Pa PWM duty 값 추출 실패 시
        # 풍량 부족과 과다의 경우를 분리하여 처리
        if not success:
            # 풍량 과다로 목표 압력보다 큰 값이 측정된 경우
            if pressure > 100:
                QMessageBox.warning(None,
                                    "풍량 과다",
                                    "풍량이 과다합니다. 팬 커버를 사용하거나 한 대의 팬만으로 시험을 진행해 주세요.")
                sensor_and_controller.duty_set(initial_duty, test=test_mode)
                return

            # 그 외의 경우는 풍량 부족으로 간주하여 최대 duty로 측정
            duty = max_duty
            success = True

        # duty 최대값 설정 완료 후 측정 수행
        if success:
            # 60Pa 측정 값 저장
            measuring["measured_value"].append([pressure, duty])
            # 측정 범위 설정
            num_to_measure = 5
            step = (duty - initial_duty) / (num_to_measure - 1)  # 간격 계산
            duty_range = [round(duty - i * step) for i in range(num_to_measure)]
            # 데이터 측정
            before = duty
            for d in duty_range:
                sensor_and_controller.duty_set(d, test=test_mode)
                print(f"wait for settle: {abs(before - d)} sec")
                time.sleep(abs(before - d))
                p = self.measuring_pressure(10, 1)
                print(f"measuring now duty={d}, pressure={p}")
                measuring["measured_value"].append([p, d])
                before = d

        # 종료 0 기류 압력 측정 # 현재 버전에서는 생략
        # measuring["final_zero_pressure"] = self.measuring_pressure(10, 1)
        # 시험 종료
        sensor_and_controller.duty_set(stop_duty, test=test_mode)
        # 시험 종료 시간 기록
        time_end = datetime.now().strftime("%H:%M:%S")
        measuring["test time"] = [time_start, time_end]

        # Raw data 백업 저장
        now = datetime.now().strftime("%y%m%d-%H%M%S")
        with open(f"./measurements/{test}_{now}.json", 'w') as file:
            json.dump(measuring, file, indent=4)
        # 데이터 저장
        with open(f"./{test}_raw.json", 'w') as file:
            json.dump(measuring, file, indent=4)

    def calculation(self):
        # 시험 조건 불러오기
        conditions = 'conditions.json'
        with open(conditions, 'r') as file:
            data = json.load(file)
        
        # 아무 시험 결과 없는 경우, Just in case.
        if not data.get("depressurization") and not data.get("pressurization"):
            pass

        # 결과 저장 변수 선언
        calculation_raw = {}
        # 보고서 용 값 저장
        calculation_raw["report"] = {}

        # 저장 할 값 지정
        need_to_save = ["C0", 
                        "n", 
                        "C0 range", 
                        "n range", 
                        "t", 
                        "variance of n", 
                        "variance of x", 
                        "mean x",
                        "N", 
                        "measured values", 
                        "margin of error of y",
                        "Q50",
                        "ACH50",
                        "AL50",
                        "r^2",
                        "Q50+-",
                        "ACH50+-",
                        "n+-",
                        "C0+-",
                        "interior_volume"]
        
        need_to_report = ["Q50", 
                          "ACH50", 
                          "AL50", 
                          "C0", 
                          "n", 
                          "Q50+-", 
                          "C0+-", 
                          "n+-", 
                          "r^2",
                          "interior_volume"]
            
        # 감압 시험을 수행 한 경우
        if data.get("depressurization"):
            # 파일 불러오기
            depressureization = ACH_calculator.BlowerDoorTestCalculator.from_file('depressurization_raw.json',
                                                                                'conditions.json')
            # 결과 계산
            results_depr = depressureization.calculate_results()
            # Raw data 저장
            now = datetime.now().strftime("%y%m%d-%H%M%S")
            with open(f"./calculations/depressurization_{now}.json", 'w') as file:
                json.dump(results_depr, file, indent=4)
            # 결과 값 변수 저장
            calculation_raw['depressurization'] = {}
            for i in results_depr.keys():
                if i in need_to_save:
                    calculation_raw['depressurization'][i]=results_depr[i]
            
            for i in need_to_report:
                report_key = i + "-"
                calculation_raw["report"][report_key] = calculation_raw["depressurization"][i]

        # 가압 시험을 수행 한 경우
        if data.get("pressurization"):
            # 파일 불러오기
            pressureization = ACH_calculator.BlowerDoorTestCalculator.from_file('pressurization_raw.json',
                                                                                'conditions.json')
            # 결과 계산
            results_pres = pressureization.calculate_results()
            # Raw data 저장
            now = datetime.now().strftime("%y%m%d-%H%M%S")
            with open(f"./calculations/pressurization_{now}.json", 'w') as file:
                json.dump(results_pres, file, indent=4)
            # 결과 값 변수 저장
            calculation_raw['pressurization'] = {}
            for i in results_pres.keys():
                if i in need_to_save:
                    calculation_raw['pressurization'][i]=results_pres[i]
            
            for i in need_to_report:
                report_key = i + "+"
                calculation_raw["report"][report_key] = calculation_raw["pressurization"][i]

        # 감/가압 시험 모두 수행 한 경우, 평균 값 계산
        if data.get("depressurization") and data.get("pressurization"):
            calculation_raw["average"] = {}
            for i in ["Q50", "ACH50", "AL50"]:
                calculation_raw["report"][i + "_avg"] = (calculation_raw["depressurization"][i] \
                                                        + calculation_raw["pressurization"][i])/2

        with open(f"./calculation_raw.json", 'w') as file:
            json.dump(calculation_raw, file, indent=4)

        print(f"{self.task_type} is done.")

    def graph_plotting(self):
        # 시험 조건 불러오기
        conditions = 'conditions.json'
        with open(conditions, 'r') as file:
            conditions = json.load(file)

        # 계산 결과 불러오기
        with open(f"./calculation_raw.json", 'r') as file:
            calculation_raw = json.load(file)

        if conditions.get("depressurization") and conditions.get("pressurization"):
            graph_plotter.plot_graph(calculation_raw['depressurization'],
                                     calculation_raw['pressurization'],
                                     calculation_raw['report'])
        elif conditions.get("depressurization"):
            graph_plotter.plot_graph(calculation_raw['depressurization'],
                                     False,
                                     calculation_raw['report'])
        elif conditions.get("pressurization"):
            graph_plotter.plot_graph(False,
                                     calculation_raw['pressurization'],
                                     calculation_raw['report'])

    def reporting(self):
        # 템플릿 파일 이름
        template_path = "report_template.xlsx"
        # 결과 파일 명  
        now = datetime.now().strftime("%y%m%d-%H%M%S")
        output_path = f"report_{now}.xlsx"
        # 이미지 정보
        image_path = "graph.png"
        cell = "B28"
        width = 590
        height = 355
        # 파일 보호 비밀번호
        key = "asdf"
        report_maker = reporting.ReportMaker(template_path)
        report_maker.process_report(output_path, image_path, cell, width, height, key)

        print(f"{self.task_type} is done.")

        # PDF 파일 만들고 열기
        import platform
        if platform.system() == "Linux":
            import subprocess as sub
            sub.call(f"libreoffice --headless --convert-to pdf {output_path}", shell=True)
            shutil.move(output_path.split('.')[0] + '.pdf', "report.pdf")
            sub.call(f"xpdf ./report.pdf", shell=True)


if __name__ == '__main__':
    sensor_and_controller.duty_set(0, False)
    app = QApplication(sys.argv)

    # 창 사이즈 설정
    size_w = 800
    size_h = 400
    # 폰트 설정
    font_db = QFontDatabase()
    # 글꼴 파일 경로
    font_id = font_db.addApplicationFont("./NanumSquare_acL.ttf")

    if font_id != -1:
        font_families = font_db.applicationFontFamilies(font_id)
        # 로드한 글꼴의 첫 번째 패밀리를 사용
        app.setFont(QFont(font_families[0], 9))
    else:
        print("Failed to load font.")

    # 메세지 종료 시간
    time_to_close = 2

    # 시험 조건 입력
    initialize = InputInitalValues()
    initialize.setWindowTitle("시험 조건 입력")
    initialize.resize(size_w, size_h)
    initialize.show()
    app.exec_()

    # 시험 조건 불러오기
    with open('conditions.json', 'r') as file:
        data = json.load(file)

    # 측정 시작 시간 저장
    time_start = datetime.now().strftime("%y/%m/%d %H:%M:%S")

    # 감압 시험
    if data.get("depressurization"):
        # 감압 시험 준비
        long_message = "측정 시작 버튼을 누르세요."
        pressure = LivePressureData(long_message)
        pressure.setWindowTitle("감압 시험 준비")
        pressure.resize(size_w, size_h)
        pressure.show()
        app.exec_()
        ###################    
        ## 데이터 측정 시작 with depressurization 파일명
        ###################    
        message = SimpleMessage("측정 중...")
        message.setWindowTitle("...")
        message.resize(size_w, size_h)
        message.show()
        wait_for_end = BackgroundTask("depressurization")
        wait_for_end.finished.connect(message.close)
        wait_for_end.start()    
        app.exec_()
        # 측정 종료
        end_of_test = SimpleMessageAutoDisappear("감압 시험 측정 완료.", time_to_close)
        end_of_test.resize(size_w, size_h)
        end_of_test.show()
        app.exec_()

    # 가압 시험
    if data.get("pressurization"):
        # 가압 시험 준비
        long_message = "측정 시작 버튼을 누르세요."
        pressure = LivePressureData(long_message)
        pressure.setWindowTitle("가압시험 준비")
        pressure.resize(size_w, size_h)
        pressure.show()
        app.exec_()
        ###################
        ## 데이터 측정 시작 with pressurization 파일명
        ###################
        message = SimpleMessage("측정 중...")
        message.setWindowTitle("...")
        message.resize(size_w, size_h)
        message.show()
        wait_for_end = BackgroundTask("pressurization")
        wait_for_end.finished.connect(message.close)
        wait_for_end.start()
        app.exec_()
        # 측정 종료
        end_of_test = SimpleMessageAutoDisappear("가압 시험 측정 완료.", time_to_close)
        end_of_test.resize(size_w, size_h)
        end_of_test.show()
        app.exec_()

    # 측정 종료 시간 저장
    time_end = datetime.now().strftime("%H:%M:%S")
    data["test_period"] = f"{time_start}~{time_end}"
    with open("conditions.json", "w") as file:
        json.dump(data, file, indent=4)

    ###################
    ## 결과 계산 코드 실행
    ###################

    # 계산 중 메시지 창
    message = SimpleMessage("시험 결과 계산 중...")
    message.setWindowTitle("...")
    message.resize(size_w, size_h)
    message.show()
    wait_for_end = BackgroundTask("calculation")
    wait_for_end.finished.connect(message.close)
    wait_for_end.start()
    app.exec_()
    # 계산 종료
    end_of_test = SimpleMessageAutoDisappear("시험 결과 계산 완료.", time_to_close)
    end_of_test.resize(size_w, size_h)
    end_of_test.show()
    app.exec_()

    ###################
    ## 그래프 작성 코드 실행
    ###################

    # 그래프 작성 메시지 창
    message = SimpleMessage("그래프 작성 중...")
    message.setWindowTitle("...")
    message.resize(size_w, size_h)
    message.show()
    # 작성 시작
    wait_for_end = BackgroundTask("graph_plotting")
    wait_for_end.finished.connect(message.close)
    wait_for_end.start()
    app.exec_()
    # 그래프 작성 종료
    end_of_test = SimpleMessageAutoDisappear("그래프 작성 완료.", time_to_close)
    end_of_test.resize(size_w, size_h)
    end_of_test.show()
    app.exec_()

    ###################
    ## 보고서 생성 코드 실행
    ###################

    # 보고서 생성 중 메시지 창
    message = SimpleMessage("보고서 생성 중...")
    message.setWindowTitle("...")
    message.resize(size_w, size_h)
    message.show()
    wait_for_end = BackgroundTask("reporting")
    wait_for_end.finished.connect(message.close)
    wait_for_end.start()
    app.exec_()
    # 보고서 생성 종료
    end_of_test = SimpleMessageAutoDisappear("보고서 생성 완료.", time_to_close)
    end_of_test.resize(size_w, size_h)
    end_of_test.show()
    app.exec_()

    # 시험 종료
    end_of_test = SimpleMessageAutoDisappear("시험이 모두 종료되었습니다.", time_to_close)
    end_of_test.resize(size_w, size_h)
    end_of_test.show()
    app.exec_()
