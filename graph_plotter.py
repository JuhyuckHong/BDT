import json
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as patches
from datetime import datetime
from matplotlib import font_manager


def log_scale_value(start, end, percent):
    log_start = np.log10(start)
    log_end = np.log10(end)

    # 해당 퍼센티지에 대한 로그 스케일 값 계산
    log_value = log_start + (log_end - log_start) * (percent)

    # 로그 스케일 값을 원래 스케일로 변환
    value = 10 ** log_value

    return value

# volumetric flow rate(㎥/h) for certain pressure
def volumetric_flow_rate(results, dp=50):
    # vfra = volumetric_flow_rate_air
    vfra = results["C0"] * math.pow(dp, results["n"])
    # 95% confidence
    vfra_min = results["C0 range"][0] * math.pow(dp, results["n range"][0])
    vfra_max = results["C0 range"][1] * math.pow(dp, results["n range"][1])
    # 95% prediction, moey = margin_of_error_of_y 
    moey = results["t"] * results["variance of n"] \
                        * math.sqrt(results["variance of x"] * (results["N"] - 1) / \
                                    results["N"] + math.pow(math.log(dp) - results["mean x"], 2)) 
    results["margin of error of y"] = moey
    return [vfra, vfra * math.exp(-moey), vfra * math.exp(moey), vfra_min, vfra_max]
    
# reverse function of volumetric_flow_rate
def reverse_vfra(results, vfra):
    # vfra = volumetric_flow_rate_air
    vfra_min = vfra / math.exp(-results["margin of error of y"])
    vfra_max = vfra / math.exp(+results["margin of error of y"])
    dp_min = math.pow(vfra_min / results["C0"], 1 / results["n"])
    dp_max = math.pow(vfra_max / results["C0"], 1 / results["n"])
    return [dp_min, dp_max]

def plot_graph(resultsd, resultsp, report):
    # 폰트 설정
    font_path = './NanumSquare_acL.ttf'
    font8 = font_manager.FontProperties(fname=font_path, size=8)
    font9 = font_manager.FontProperties(fname=font_path, size=9)
    font10 = font_manager.FontProperties(fname=font_path, size=10)
    

    # 창 크기 고정 - 픽셀 단위
    width_px = 2400  
    height_px = 1500  
    dpi = 300  # 인치당 픽셀 (dots per inch)
    plt.figure(figsize=(width_px/dpi, height_px/dpi))
    
    # ACH50 표시
    position = {"x": 10.5,
                "y": 110}
    text = {"s": f'[ACH50]'}
    if resultsd and resultsp:
        text["s"] += f'\n평균: {report["ACH50_avg"]:.2f}'
        text["s"] += f'\n감압: {report["ACH50-"]:.2f}'
        text["s"] += f'\n가압: {report["ACH50+"]:.2f}'
        text["s"] += f'\n체적: {report["interior_volume-"]:.1f}㎥'
    elif resultsd:
        text["s"] += f'\n감압: {report["ACH50-"]:.2f}'
        text["s"] += f'\n내부체적: {report["interior_volume-"]:.1f}㎥'
    elif resultsp:
        text["s"] += f'\n가압: {report["ACH50+"]:.2f}'
        text["s"] += f'\n체적: {report["interior_volume+"]:.1f}㎥'
    
    plt.text(**position,
             **text, 
             fontproperties=font10, 
             ha='left',
             bbox=dict(facecolor='white',
                       edgecolor='grey',
                       boxstyle='round',
                       pad=0.25,
                       alpha=0.5,
                       linewidth=1,
                       linestyle='--'))

    # x 축 설정
    plt.xscale("log")
    plt.xticks([10, 20, 30, 40, 50, 60, 70, 80, 90, 100], 
               [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    plt.tick_params(axis='x', direction='in')
    x_lim_min = 10
    x_lim_max = 100
    plt.xlim(x_lim_min, x_lim_max)

    # y 축 설정
    plt.yscale("log")
    plt.yticks([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
               [100, 200, 300, 400, 500, 600, 700, 800, 900, '1,000'])
    plt.tick_params(axis='y', direction='in')
    y_lim_min = 100
    y_lim_max = 1000
    plt.ylim(y_lim_min, y_lim_max)

    equation = r'$Q={C:.2f} \cdot \Delta P^{{{n:.2f}}}$'
    # 그래프 그리기 옵션들
    if resultsd:
        Q50_marker_d = {
            "marker": '*',
            "s": 50,
            "edgecolor": "black",
            "color": 'red',
            "zorder": 11
        }
        scatter_params_d = {
            'label': "감압 측정 값",
            'color': (0.3, 0.1, 0.1, 0.5),
            'marker': 'v',
            's': 30,
            'zorder': 10
        }
        derived_params_d = {
            'label': equation.format(C=resultsd['C0'], n=resultsd['n']),
            'color': (1,0,0,0.8),
            'linewidth': 1.5,
            'alpha': 1,
            'zorder': 9
        }
        derived_params_d_ax = {
            'color': (1,0,0,0.8),
            'linewidth': 0.5,
            'alpha': 1,
            'zorder': 9
        }
        marker_enlarge_95_d = {
            "color": "red",
            "marker": '_',
            "s": 50,
            "zorder": 11}
        marker_enlarge_ACH_d = {
            "color": "red",
            "edgecolor": "black",
            "marker": (5, 1),
            "s": 50,
            "zorder": 11}

    if resultsp:
        Q50_marker_p = {
            "marker": '*',
            "s": 50,
            "edgecolor": "black",
            "color": 'blue',
            "zorder": 11
        }
        scatter_params_p = {
            'label': "가압 측정 값",
            'color': (0.1, 0.1, 0.3, 0.5),
            'marker': '^',
            's': 30,
            'zorder': 10
        }
        derived_params_p = {
            'label': equation.format(C=resultsp['C0'], n=resultsp['n']),
            'color': (0,0,1,0.8),
            'linewidth': 1.5,
            'alpha': 1,
            'zorder': 9
        }
        derived_params_p_ax = {
            'color': (0,0,1,0.8),
            'linewidth': 0.5,
            'alpha': 1,
            'zorder': 9
        }
        marker_enlarge_95_p = {
            "color": "blue",
            "marker": '_',
            "s": 50,
            "zorder": 11}
        marker_enlarge_ACH_p = {
            "color": "blue",
            "edgecolor": "black",
            "marker": (5, 1),
            "s": 50,
            "zorder": 11}

    ci_params = {
        'color': 'green',
        'linewidth': 0.5,
        'alpha': 1,
        'linestyle': '-',
        'zorder': 8
    }
    pi_params = {
        'color': 'blue',
        'linewidth': 0.1,
        'alpha': 1,
        'linestyle': '-',
        'zorder': 8
    }
    fill_params_CI = {
        'color': 'green',
        'alpha': 0.1,
        'zorder': 8
    }
    fill_patch_CI = {
        'facecolor': 'green',
        'alpha': 0.2,
        'label': '95% 신뢰구간',
        'zorder': 9
    }
    fill_params_PI = {
        'color': 'grey',
        'alpha': 0.05,
        'hatch': '\\',
        'zorder': 8
    }
    fill_patch_PI = {
        'color': 'grey',
        'hatch': '\\',
        'alpha': 0.1,
        'label': '95% 예측구간',
        'zorder': 8
    }

    # 그래프 그리기
    
    # 데이터 플롯
    Pa_50 = 50

    xd = range(10, 110)
    xp = xd
    ## depress
    if resultsd:
        # 측정값
        xd_values, yd_values = zip(*resultsd["measured values"])
        # 계산값(ci=95%신뢰구간, pi=95%예측구간)
        # xd = range(int(min(xd_values) - 4), int(max(xd_values) + 15))
        yd, yd_ci_l, yd_ci_u, yd_pi_l, yd_pi_u = zip(*[volumetric_flow_rate(resultsd, i) for i in xd])
        plt.scatter(xd_values, yd_values, **scatter_params_d)
        plt.plot(xd, yd, **derived_params_d)
        plt.plot(xd, yd_pi_l, **pi_params)
        plt.plot(xd, yd_pi_u, **pi_params)
        plt.plot(xd, yd_ci_l, **ci_params)
        plt.plot(xd, yd_ci_u, **ci_params)
        plt.fill_between(xd, yd_pi_l, yd_pi_u, **fill_params_PI)
        plt.fill_between(xd, yd_ci_l, yd_ci_u, **fill_params_CI)

    ## press
    if resultsp:
        # 측정값
        xp_values, yp_values = zip(*resultsp["measured values"])
        # 계산값(ci=95%신뢰구간, pi=95%예측구간)
        # xp = range(int(min(xp_values) - 4), int(max(xp_values) + 15))
        yp, yp_ci_l, yp_ci_u, yp_pi_l, yp_pi_u = zip(*[volumetric_flow_rate(resultsp, i) for i in xp])
        plt.scatter(xp_values, yp_values, **scatter_params_p)
        plt.plot(xp, yp, **derived_params_p)
        plt.plot(xp, yp_pi_l, **pi_params)
        plt.plot(xp, yp_pi_u, **pi_params)
        plt.plot(xp, yp_ci_l, **ci_params)
        plt.plot(xp, yp_ci_u, **ci_params)
        plt.fill_between(xp, yp_pi_l, yp_pi_u, **fill_params_PI)
        plt.fill_between(xp, yp_ci_l, yp_ci_u, **fill_params_CI)

    # 보조선 추가
    plt.grid(True, which="both", linestyle="--", linewidth=1, color="gray", alpha=0.5)

    # 축 레이블 설정
    plt.xlabel('압력차 [Pa]',
               labelpad=15,
               fontproperties=font10)
    plt.ylabel('침기량\n(누기량)\n[㎥/h]',
               rotation='horizontal',
               labelpad=20,
               linespacing=2,
               fontproperties=font10)

    # 그래프와 제목 사이 간격 조정
    plt.subplots_adjust(top=0.9, bottom=0.15, left=0.15)
    
    # 기존 범례 가져오기
    handles, labels = plt.gca().get_legend_handles_labels()

    # 채우기(95% 신뢰, 예측) 범례 생성
    fill_ci = mpatches.Patch(**fill_patch_CI)
    handles.append(fill_ci)
    labels.append(fill_ci.get_label())    
    fill_pi = mpatches.Patch(**fill_patch_PI)
    handles.append(fill_pi)
    labels.append(fill_pi.get_label())

    # 범례 표시
    legend = plt.legend(handles, labels, loc="upper left", prop=font9)
    legend.get_frame().set_facecolor((0.98,0.98,0.98))
    legend.set_zorder(20)
    

    # 50 Pa 라인 그리기
    plt.axvline(x=Pa_50, color='green', linewidth=0.3, linestyle='-')
    # 감압 Q50 라인, 마커  그리기
    if resultsd:
        Q50d = volumetric_flow_rate(resultsd, Pa_50)[0]
        plt.axhline(y=Q50d, color='green', linewidth=0.3, linestyle='-')
        plt.scatter(Pa_50, Q50d, **Q50_marker_d)
    # 가압 Q50 라인, 마커 그리기
    if resultsp:
        Q50p = volumetric_flow_rate(resultsp, Pa_50)[0]
        plt.axhline(y=Q50p, color='green', linewidth=0.3, linestyle='-')
        plt.scatter(Pa_50, Q50p, **Q50_marker_p)
    

    # 확대 할 범위 계산 
    # 감압
    if resultsd:
        xd_closeup_start = max(reverse_vfra(resultsd, Q50d)[1], 10)
        xd_closeup_end = min(reverse_vfra(resultsd, Q50d)[0], 100)
        yd_closeup_start = max(volumetric_flow_rate(resultsd, Pa_50)[1], 100)
        yd_closeup_end = min(volumetric_flow_rate(resultsd, Pa_50)[2], 1000)

        # 감압 확대 플롯 위치 사각형 그리기
        rectd = patches.Rectangle((xd_closeup_start, yd_closeup_start), 
                                xd_closeup_end - xd_closeup_start, 
                                yd_closeup_end - yd_closeup_start, 
                                linewidth=1, edgecolor='r', facecolor='none')
        plt.gca().add_patch(rectd)
    # 가압
    if resultsp:
        xp_closeup_start = max(reverse_vfra(resultsp, Q50p)[1], 10)
        xp_closeup_end = min(reverse_vfra(resultsp, Q50p)[0], 100)
        yp_closeup_start = max(volumetric_flow_rate(resultsp, Pa_50)[1], 100)
        yp_closeup_end = min(volumetric_flow_rate(resultsp, Pa_50)[2], 1000)

        # 가압 확대 플롯 위치 사각형 그리기
        rectp = patches.Rectangle((xp_closeup_start, yp_closeup_start), 
                                xp_closeup_end - xp_closeup_start, 
                                yp_closeup_end - yp_closeup_start, 
                                linewidth=1, edgecolor='b', facecolor='none')
        plt.gca().add_patch(rectp)
    
    if resultsd:
        # 감압 axd=depress 확대 플롯 위치, 크기 설정
        leftd = 0.50
        bottomd = 0.2
        widthd = 0.15
        heightd = 0.15

        # 확대 플롯 화살표 그리기
        ## 감압 depress 화살표 좌표값 계산
        x1d = log_scale_value(x_lim_min, x_lim_max, leftd + widthd/2)
        y1d = log_scale_value(y_lim_min, y_lim_max, (bottomd + heightd)-0.08)
        x2d = (xd_closeup_start + xd_closeup_end)/2
        y2d = yd_closeup_start
        ## 화살표 그리기
        plt.annotate('',  # 표시할 텍스트 
                    xy=(x1d, y1d),  # 화살표 머리 위치
                    xytext=(x2d, y2d),  # 화살표 꼬리 위치
                    arrowprops=dict(facecolor='red',
                                    edgecolor='red',
                                    arrowstyle='->')
        )
    if resultsp:
        # 가압 axp=press 확대 플롯 위치, 크기 설정
        leftp = 0.68
        bottomp = 0.2
        widthp = 0.15
        heightp = 0.15

        ## 가압 press 화살표 좌표값 계산
        x1p = log_scale_value(x_lim_min, x_lim_max, leftp + widthp/2+0.05)
        y1p = log_scale_value(y_lim_min, y_lim_max, (bottomp + heightp)-0.08)
        x2p = (xp_closeup_start + xp_closeup_end)/2
        y2p = yp_closeup_start
        ## 화살표 그리기
        plt.annotate('',  # 표시할 텍스트 
                    xy=(x1p, y1p),  # 화살표 머리 위치
                    xytext=(x2p, y2p),  # 화살표 꼬리 위치
                    arrowprops=dict(facecolor='blue',
                                    edgecolor='blue',
                                    arrowstyle='->')
        )

    if resultsd:
        # axd=depress 확대 플롯 위치
        axd = plt.axes([leftd, bottomd, widthd, heightd]) 

        # 확대 플롯 축 설정
        axd.set_xscale("log")
        axd.set_yscale("log")
        axd.set_xlim(xd_closeup_start, 
                    xd_closeup_end)
        axd.set_ylim(yd_closeup_start - (Q50d - yd_closeup_start)*0.1, 
                    yd_closeup_end + (yd_closeup_end - Q50d)*0.1)

        # 확대 플롯 틱
        axd.set_xticks([Pa_50], [""])
        axd.set_yticks([yd_closeup_start, 
                    yd_closeup_end], 
                    [f'{yd_closeup_start:.0f}',
                    f'{yd_closeup_end:.0f}'])

        # 확대 플롯 그리기
        axd.plot(xd, yd, **derived_params_d_ax)
        axd.plot(xd, yd_pi_l, **ci_params)
        axd.plot(xd, yd_pi_u, **ci_params)
        axd.plot(xd, yd_ci_l, **pi_params)
        axd.plot(xd, yd_ci_u, **pi_params)
        axd.scatter(xd_values, yd_values, **scatter_params_d)
        
        # 예측구간 사이 영역 색칠
        axd.fill_between(xd, yd_pi_l, yd_pi_u, **fill_params_PI)
        # 신뢰구간 사이 영역 색칠
        axd.fill_between(xd, yd_ci_l, yd_ci_u, **fill_params_CI)

        # 자동생성 틱 삭제
        axd.yaxis.set_minor_locator(plt.NullLocator())
        axd.xaxis.set_minor_locator(plt.NullLocator())

        # 틱 설정
        axd.tick_params(axis='x', 
                        which='both', 
                        bottom=1, 
                        top=0, 
                        labelbottom=1, 
                        labeltop=0)
        axd.tick_params(axis='y', 
                        which='both', 
                        left=1, 
                        right=0, 
                        labelleft=1, 
                        labelright=0,
                        labelsize=8)
        axd.tick_params(axis='both', 
                        which='both', 
                        pad=5, 
                        labelcolor='black', 
                        direction='inout', 
                        width=1, 
                        length=5)

        ## 계산된 Q50과 95% 신뢰값 표시
        ### Q50
        offset_xd = (xd_closeup_end - Pa_50)/10
        offset_yd = (yd_closeup_end - Q50d)/5    
        axd.scatter(Pa_50, Q50d, **marker_enlarge_ACH_d)
        axd.text(Pa_50 + offset_xd, Q50d - offset_yd,
                f'{Q50d:.2f}㎥/h',
                weight='bold',
                fontproperties=font8,
                bbox=dict(facecolor=(0.9, 0.9, 0.7, 0.5),
                        edgecolor=(0.9, 0.9, 0.7, 0.5),
                        pad=0.05,
                        boxstyle='round,pad=0.2'))
        ### 95% 신뢰값 Q50
        axd.scatter(Pa_50, yd_closeup_end, **marker_enlarge_95_d)
        axd.scatter(Pa_50, yd_closeup_start, **marker_enlarge_95_d)

        # x = 50 세로줄 긋기
        axd.axvline(x=Pa_50, color='red', linewidth=1, linestyle='--')

        # 레이블 배경 설정
        labelsd = axd.get_xticklabels() + axd.get_yticklabels()  # X와 Y 레이블 모두 가져오기
        plt.setp(labelsd, backgroundcolor=(1,1,1,0.5))  # 배경색을 흰색으로 설정

    if resultsp:
        # axp=press 확대 플롯 위치
        axp = plt.axes([leftp, bottomp, widthp, heightp]) 

        # 확대 플롯 축 설정
        axp.set_xscale("log")
        axp.set_yscale("log")
        axp.set_xlim(xp_closeup_start, 
                    xp_closeup_end)
        axp.set_ylim(yp_closeup_start - (Q50p - yp_closeup_start)*0.1, 
                    yp_closeup_end + (yp_closeup_end - Q50p)*0.1)

        # 확대 플롯 틱
        axp.set_xticks([Pa_50], [""])
        axp.set_yticks([yp_closeup_start, 
                    yp_closeup_end], 
                    [f'{yp_closeup_start:.0f}',
                    f'{yp_closeup_end:.0f}'])

        # 확대 플롯 그리기
        axp.plot(xp, yp, **derived_params_p_ax)
        axp.plot(xp, yp_pi_l, **ci_params)
        axp.plot(xp, yp_pi_u, **ci_params)
        axp.plot(xp, yp_ci_l, **pi_params)
        axp.plot(xp, yp_ci_u, **pi_params)
        axp.scatter(xp_values, yp_values, **scatter_params_p)
        
        # 예측구간 사이 영역 색칠
        axp.fill_between(xp, yp_pi_l, yp_pi_u, **fill_params_PI)
        # 신뢰구간 사이 영역 색칠
        axp.fill_between(xp, yp_ci_l, yp_ci_u, **fill_params_CI)

        # 자동생성 틱 삭제
        axp.yaxis.set_minor_locator(plt.NullLocator())
        axp.xaxis.set_minor_locator(plt.NullLocator())

        # 틱 설정
        axp.tick_params(axis='x', 
                        which='both', 
                        bottom=1, 
                        top=0, 
                        labelbottom=1, 
                        labeltop=0)
        axp.tick_params(axis='y', 
                        which='both', 
                        left=0, 
                        right=1, 
                        labelleft=0, 
                        labelright=1,
                        labelsize=8)
        axp.tick_params(axis='both', 
                        which='both', 
                        pad=5, 
                        labelcolor='black', 
                        direction='inout', 
                        width=1, 
                        length=5)

        ## 계산된 Q50과 95% 신뢰값 표시
        ### Q50
        offset_xp = (xp_closeup_end - Pa_50)/10
        offset_yp = (yp_closeup_end - Q50p)/5    
        axp.scatter(Pa_50, Q50p, **marker_enlarge_ACH_p)
        axp.text(Pa_50 + offset_xp, Q50p - offset_yp,
                f'{Q50p:.2f}㎥/h',
                weight='bold',
                fontproperties=font8,
                bbox=dict(facecolor=(0.9, 0.9, 0.7, 0.5),
                        edgecolor=(0.9, 0.9, 0.7, 0.5),
                        pad=0.05,
                        boxstyle='round,pad=0.2'))
        ### 95% 신뢰값 Q50
        axp.scatter(Pa_50, yp_closeup_end, **marker_enlarge_95_p)
        axp.scatter(Pa_50, yp_closeup_start, **marker_enlarge_95_p)

        # x = 50 세로줄 긋기
        axp.axvline(x=Pa_50, color='red', linewidth=1, linestyle='--')

        # 레이블 배경 설정
        labelsp = axp.get_xticklabels() + axp.get_yticklabels()  # X와 Y 레이블 모두 가져오기
        plt.setp(labelsp, backgroundcolor=(1,1,1,0.5))  # 배경색을 흰색으로 설정

    # 백업 저장
    now = datetime.now().strftime("%d%m%Y-%H%M%S")
    plt.savefig(f'./graphs/graph_{now}.png', dpi=300, bbox_inches='tight')
    # 사용할 그래프 저장
    plt.savefig(f'./graph.png', dpi=300, bbox_inches='tight')

if __name__ == '__main__':

    # 시험 조건 불러오기
    conditions = 'conditions.json'
    with open(conditions, 'r') as file:
        conditions = json.load(file)

    # 계산 결과 불러오기
    with open(f"./calculation_raw.json", 'r') as file:
        calculation_raw = json.load(file)

    if conditions.get("depressurization") and conditions.get("pressurization"):
        plot_graph(calculation_raw['depressurization'],
                   calculation_raw['pressurization'],
                   calculation_raw['report'])
    elif conditions.get("depressurization"):
        plot_graph(calculation_raw['depressurization'], 
                   False,
                   calculation_raw['report'])
    elif conditions.get("pressurization"):
        plot_graph(False,
                   calculation_raw['pressurization'],
                   calculation_raw['report'])
