import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from dotenv import load_dotenv
    from zeppfit.api import Api
    from zeppfit.scraper import Scraper
    from zeppfit.exporters.gpx_exporter import GpxExporter
    import os
    import pandas as pd
    import plotly.express as px
    from typing import List, Annotated
    from pydantic import Field


    API = "https://api-mifit.huami.com"
    ok = load_dotenv(".env")
    if not ok:
        raise EnvironmentError("Missing environment variables")
    return (
        API,
        Annotated,
        Api,
        Field,
        GpxExporter,
        List,
        Scraper,
        mo,
        os,
        pd,
        px,
    )


@app.cell
def _(API, Api, GpxExporter, Scraper, os):
    from pathlib import Path

    api = Api(API, os.environ["ZEPP_TOKEN"])
    exporter = GpxExporter()
    scraper = Scraper(api, exporter, Path("./zepp_workouts"), "gpx")
    return (api,)


@app.cell
def _(api):
    history = api.get_workout_history()
    return (history,)


@app.cell
def _():
    import json

    # os.makedirs("summaries", exist_ok=True)
    # for s in history.data.summary:
    #     with open(f"summaries/{s.end_time}_{s.trackid}.json", "w") as f:
    #         json.dump(s.model_dump(), f, indent=2)
    return


@app.cell
def _(history):
    from pprint import pprint

    print("Fecthed all activities?", history.data.next == -1)
    history.data.summary
    print(f"Total activity count: {len(history.data.summary)}")

    # pprint(f"Summary attrs", )
    activity = history.data.summary[0]
    #pprint(activity.__dict__)


    # Type
    type = activity.type
    unit = activity.unit
    version = activity.version

    auto_recognised = activity.auto_recognition  # AI that starts activity automatically
    avg_hr = activity.avg_heart_rate
    max_hr = activity.max_heart_rate
    min_hr = activity.min_heart_rate
    avg_frequency = activity.avg_frequency # ?? steps or hr?
    calories = activity.calorie
    city = activity.city
    distance = activity.dis

    start_time = activity.trackid
    end_time = activity.end_time

    pause_time = activity.pause_time
    activity.heartrate_setting_type # ??
    activity.location # ??

    # Rope
    rscount = activity.rope_skipping_count
    rsavgfreq = activity.rope_skipping_avg_frequency
    rsrt = activity.rope_skipping_rest_time
    rsmfreq = activity.rope_skipping_max_frequency

    duration = activity.run_time

    # Source
    device = activity.source

    # Training effects
    aerobic_effect = activity.te
    anaerobic_effect = activity.anaerobic_te

    steps = activity.total_step
    return (pprint,)


@app.cell
def _(history):
    import datetime as dt
    workouts = [workout for workout in history.data.summary]

    workout = workouts[0]

    start = dt.datetime.fromtimestamp(int(workout.trackid))
    end = dt.datetime.fromtimestamp(int(workout.end_time))

    print(f"Activity type {workout.type} {start} {end}")
    return dt, workout


@app.cell
def _(List):
    def decode_hr(hr_string: str) -> List[int]:
        """
        Decode Amazfit heart rate string into absolute HR values.

        Parameters
        ----------
        hr_string : str
            Heart rate string in Amazfit delta format, e.g. "0,136;23,-20;,..."

        Returns
        -------
        List[int]
            Absolute heart rate values
        """
        if not hr_string:
            return []

        hr_values = []
        current_hr = None

        for pair in filter(None, hr_string.split(";")):
            parts = pair.split(",")
            if len(parts) == 2:
                delta = int(parts[1])
                if current_hr is None:
                    current_hr = delta  # first value is absolute
                else:
                    current_hr += delta
            elif len(parts) == 1 and parts[0]:
                delta = int(parts[0])
                if current_hr is None:
                    current_hr = delta
                else:
                    current_hr += delta
            else:
                continue
            hr_values.append(current_hr)

        return hr_values
    return (decode_hr,)


@app.cell
def _(api, decode_hr, pd, px, workout):
    detail = api.get_workout_detail(workout)
    hr_ts = decode_hr(detail.data.heart_rate)

    def draw_activity_hr(heart_rate_data):
        df = pd.DataFrame({
            "Time (s)": range(len(hr_ts)),
            "Heart Rate (BPM)": hr_ts
        })
        fig = px.line(
            df,
            x="Time (s)",
            y="Heart Rate (BPM)",
            title="Heart Rate Time Series",
            line_shape="spline",   # smooth curve like HR charts
        )
        fig.add_traces(
               px.area(df, x="Time (s)", y="Heart Rate (BPM)", line_shape="spline").update_traces(
                    line=dict(color="#FF6B6B"),
                    fillcolor="rgba(255,107,107,0.3)"  # lighter red with transparency
                ).data
        )
        fig.update_traces(line=dict(color="red", width=2))
        fig.update_layout(
            template="plotly_dark",
            title="Heart Rate Time Series",
            xaxis_title="Time (samples)",
            yaxis_title="Heart Rate (BPM)",
            yaxis=dict(range=[50, max(hr_ts) + 10]),
            showlegend=False
        )
        fig.show()

    draw_activity_hr(hr_ts)
    return


@app.cell
def _(Annotated, Field, api, decode_hr, dt, pprint, workout):
    from pydantic import BaseModel

    # pprint(workout.model_dump())
    w = workout
    _detail = api.get_workout_detail(workout)
    _hr_ts = decode_hr(_detail.data.heart_rate)

    class PadelActivity(BaseModel):
        start: int
        end: int
        duration_minutes: int
        shots_drive: int
        shots_back: int
        shots_total: int
        hr_max: int
        hr_avg: int
        hr_ts: Annotated[list[int], Field(repr=False)]
        calories: int
        aerobic_effect: int
        anaerobic_effect: int


    p = PadelActivity(
        start=w.trackid,
        end=w.end_time,
        duration_minutes=int(int(w.run_time) / 60),
        shots_drive=w.fore_hand,
        shots_back=w.back_hand,
        shots_total=w.strokes,
        hr_max=w.max_heart_rate,
        hr_avg=w.avg_heart_rate,
        hr_ts=_hr_ts,
        calories=w.calorie,
        aerobic_effect=w.te,
        anaerobic_effect=w.anaerobic_te,
    )
    pprint(p)
    print(p.start)
    print(dt.datetime.fromtimestamp(p.start))
    # print(dt.datetime.fromtimestamp(p.start * 1000))
    return PadelActivity, p


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Fit Builder""")
    return


@app.cell
def _(PadelActivity, p):
    from fit_tool.fit_file_builder import FitFileBuilder
    from fit_tool.profile.messages.session_message import SessionMessage
    from fit_tool.profile.profile_type import Sport
    from fit_tool.fit_file_builder import FitFileBuilder
    from fit_tool.profile.messages.file_id_message import FileIdMessage
    from fit_tool.profile.messages.record_message import RecordMessage
    from fit_tool.profile.messages.workout_message import WorkoutMessage
    from fit_tool.profile.messages.session_message import SessionMessage
    from fit_tool.profile.messages.workout_step_message import WorkoutStepMessage
    from fit_tool.profile.profile_type import (
        Sport, Intensity, WorkoutStepDuration, WorkoutStepTarget, Manufacturer,
        FileType,
    )


    def export_minimal_fit(p: PadelActivity, out_file: str):
        # We set autoDefine to true, so that the builder creates the required
        # Definition Messages for us.
        builder = FitFileBuilder(auto_define=True, min_string_size=50)

    
        file_id_message = FileIdMessage()
        file_id_message.type = FileType.ACTIVITY
        file_id_message.manufacturer = Manufacturer.DEVELOPMENT
        file_id_message.product = 1
        file_id_message.time_created = p.start * 1000
        file_id_message.serial_number = 0x12345678
    
        session_msg = SessionMessage()
        session_msg.sport = Sport.TENNIS
        session_msg.start_time = p.start * 1000
        session_msg.total_elapsed_time = p.duration_minutes * 60  # Total Time including pauses
        session_msg.total_timer_time = p.duration_minutes * 60  # Activity Time
        session_msg.total_calories = p.calories
        session_msg.avg_heart_rate = p.hr_avg
        session_msg.max_heart_rate = p.hr_max
        session_msg.total_training_effect = p.aerobic_effect / 10
        session_msg.total_anaerobic_training_effect = p.anaerobic_effect / 10

    
        builder.add(file_id_message)
        builder.add(session_msg)
        for i, hr in enumerate(p.hr_ts):
            record = RecordMessage()
            record.timestamp = (p.start * 1000) + (i * 1000)
            record.heart_rate = hr
            builder.add(record)
    
        fit_file = builder.build()

        out_path = 'example_with_hr.fit'
        fit_file.to_file(out_path)



    export_minimal_fit(p, "a.fit")
    return


if __name__ == "__main__":
    app.run()
