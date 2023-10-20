# folium
import folium      
import folium.plugins

import os, io, sys
import ast
import folium.plugins
import sqlite3  
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Qt5Agg")      
import matplotlib.pyplot as plt
from shapely.geometry import Polygon


from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplitter, QVBoxLayout,QSpacerItem,QSizePolicy, QScrollArea,
                             QWidget, QLabel, QListWidget, QAbstractItemView, QHBoxLayout )
from PyQt6.QtWebEngineWidgets import QWebEngineView 


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        dpath = './data/db/livestocks.db'
        conn = sqlite3.connect(dpath)

        self.df = pd.read_sql_query('SELECT prt_type_nm, sig_kor_nm, geom_coordinates FROM LIVESTOCKS', conn)
        self.df_col_sig = pd.read_sql_query("SELECT DISTINCT sig_kor_nm FROM LIVESTOCKS", conn)
        self.df_col_prt = pd.read_sql_query("SELECT DISTINCT prt_type_nm FROM LIVESTOCKS", conn)

        m = folium.Map(location=[36.429,127.977],scrollWheelZoom=True, tiles='cartodbdark_matter', zoom_start=6)  # 지도 초기값  cartodbdark_matter
        html_string = m.get_root().render()
        self.web_view = QWebEngineView()
        self.web_view.setHtml(html_string)
        self.web_view.setMinimumSize(400, 300)
        
        self.color_mapping = {'미식별': 'green',  # 연녹색
                              '닭': 'yellow',     # 노란색
                              '돼지': 'pink',   # 분홍색
                              '소': 'blue',     # 청록색 
                            }
        self.initUI()


    def initUI(self):
        # 메인 위젯 설정
        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)

        self.setCentralWidget(main_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal, self) 

        sidebar = self.initSidebar()
        splitter.addWidget(sidebar) 

        # 메인보드 생성
        mainboard = self.initMainboard()
        splitter.addWidget(mainboard)  # QSplitter에 메인보드 추가

        # 오른쪽 화면 구성
        main_layout.addWidget(splitter)

        # 기본구성
        self.setGeometry(2000, 200, 900, 500)
        self.show()


    def initSidebar(self):
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)

        # QListWidget for 지역 선정
        sidebar_layout.addWidget(QLabel("지역을 선택하세요"))
        self.state_listwidget = QListWidget()
        self.state_listwidget.setFixedHeight(275) 
        self.state_listwidget.addItems(['전체'] + sorted(self.df_col_sig['sig_kor_nm']))            # 성능개선-1013
        self.state_listwidget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.state_listwidget.itemSelectionChanged.connect(self.update_table)
        sidebar_layout.addWidget(self.state_listwidget)

        # QListWidget for 축사종류 선정
        sidebar_layout.addWidget(QLabel("축사 종류를 선택하세요"))
        self.livestock_listwidget = QListWidget()
        self.livestock_listwidget.setFixedHeight(95)
        self.livestock_listwidget.addItems(['전체'] + sorted(self.df_col_prt['prt_type_nm']))       # 성능개선-1013
        self.livestock_listwidget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.livestock_listwidget.itemSelectionChanged.connect(self.update_table)
        sidebar_layout.addWidget(self.livestock_listwidget)

        # 빈 공간 생성하여 공간확보
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sidebar_layout.addItem(spacer)

        # 스크롤 옵션 제거하는 경우, return은 sidebar로 변경 필요
        scroll = QScrollArea()
        scroll.setWidget(sidebar)
        scroll.setWidgetResizable(True)

        return scroll  #sidebar


    def initMainboard(self):
        mainboard = QWidget()
        mainboard_layout = QVBoxLayout(mainboard)

        # (구역 1) 지도 표출 화면 구성
        label = QLabel("지역별 축사현황 지도")            # mainboard_layout.addWidget(QLabel("지역별 축사현황 지도"))
        mainboard_layout.addWidget(label)            # 라벨 반영
        mainboard_layout.addWidget(self.web_view,1)  # 지도 반영

        # (구역 2) 화면 구성 
        graph_layout = QHBoxLayout()
        mainboard_layout.addLayout(graph_layout)
        mainboard_layout.addWidget(self.web_view)
     
        return mainboard
    

    def update_table(self):
        selected_states = [item.text() for item in self.state_listwidget.selectedItems()]
        selected_livestocks = [item.text() for item in self.livestock_listwidget.selectedItems()]

        self.display_map(self.df, selected_states, selected_livestocks, self.color_mapping)

    def display_map(self, df, selected_states, selected_livestocks, color_mapping):
        if '전체' not in selected_states:
            df = df[df['sig_kor_nm'].isin(selected_states)]
        if '전체' not in selected_livestocks:
            df = df[df['prt_type_nm'].isin(selected_livestocks)]

        df_copy = df.copy()
        df_copy.loc[:, 'geometry'] = df_copy['geom_coordinates'].apply(lambda x: Polygon(ast.literal_eval(x)[0]) if pd.notnull(x) else None)
        df = df_copy
        gdf = gpd.GeoDataFrame(df, geometry='geometry')

        m = folium.Map(location=[36.429, 127.977], scrollWheelZoom=True, tiles='cartodbdark_matter', zoom_start=6)  # MapQuest Open Aerial /cartodbdark_matter

        geojson_data = gdf.to_json()
        folium.GeoJson(geojson_data,
                       style_function=lambda x: {
                           'color': color_mapping.get(x['properties']['prt_type_nm'], 'gray')
                           }).add_to(m)

   
        html_string = m.get_root().render()
        self.web_view.setHtml(html_string)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApp()
    sys.exit(app.exec())