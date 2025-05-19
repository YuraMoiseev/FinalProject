use pyo3::prelude::*;
use pyo3::pyclass;
use rayon::prelude::*;
use std::collections::HashMap;

#[pyclass]
#[derive(Debug, Clone, Copy)]
pub struct Params {
    pub s: f64,
    pub x0: f64,
    pub y0: f64,
    pub w: f64,
    pub a: f64,
    pub b: f64,
}

pub mod wasc {
    pub const E: f64 = std::f64::consts::E;
    pub const D: super::Params = super::Params {
        s: 2.0,
        x0: 0.02,
        y0: 0.1,
        w: 25.0,
        a: 3.0,
        b: 10.0,
    };

    pub const N: super::Params = super::Params {
        s: 5.0,
        x0: 0.05,
        y0: 0.1,
        w: 10.0,
        a: 2.0,
        b: 10.0,
    };

    pub const T: super::Params = super::Params {
        s: 0.3,
        x0: 0.1,
        y0: 0.1,
        w: 3.0,
        a: 5.0,
        b: 10.0,
    };
}

#[pyclass]
#[derive(Clone, Debug)]
struct MIDITrack {
    notes: Vec<f64>,
    times: Vec<f64>,
    directions: Vec<f64>,
    resolution: f64,
}

// Constructor for `MidiTrack`
#[pymethods]
impl MIDITrack {
    #[new]
    fn new(notes: Vec<f64>, times: Vec<f64>, directions: Vec<f64>, resolution: f64) -> Self {
        MIDITrack { notes, times, directions, resolution }
    }
}

// impl<'a> FromPyObject<'a> for MIDITrack {
//     fn extract(ob: &'a PyAny) -> PyResult<Self> {
//         let notes = ob.get_item(0)?
//             .extract::<Vec<f64>>()?;
//         let times = ob.get_item(1)?
//             .extract::<Vec<f64>>()?;
//         let directions = ob.get_item(2)?
//             .extract::<Vec<f64>>()?;

//         Ok(MIDITrack {
//             notes,
//             times,
//             directions,
//         })
//     }
// }

#[pyclass]
struct MidiDTW {
    param_types: HashMap<String, Params>,
}

#[pymethods]
impl MidiDTW {
    #[new]
    fn new() -> Self {
        let mut param_types = HashMap::new();
        param_types.insert("notes".into(), wasc::N);
        param_types.insert("timings".into(), wasc::T);
        param_types.insert("directions".into(), wasc::D);
        MidiDTW { param_types }
    }

    fn compare_midis(
        &self,
        user_sequences: Vec<MIDITrack>,
        song_sequences: Vec<MIDITrack>
    ) -> (f64, (usize, usize), f64) {
        let mut result = (-1.0, (0, 0), -1.0);

        song_sequences.iter().enumerate().for_each(
            |(i, song_track)| {
            user_sequences.iter().enumerate().for_each(
                |(j, user_track)| {
                let (dist, time) = self.compare_tracks(&user_track, &song_track);
                if dist < result.0 || result.0 == -1.0 {
                    result = (dist, (i, j), time);
                }
            });
        });

        result
    }

    fn compare_tracks(
        &self,
        user_track: &MIDITrack,
        song_track: &MIDITrack
    ) -> (f64, f64) {
        if user_track.notes.len() >= song_track.notes.len() {
            self.compare_full_sequence(user_track, song_track)
        } else {
            self.compare_sliding_window(user_track, song_track)
        }
    }

    /// Compute the best DTW distance by sliding a window (of length equal to `seq1`)
    /// over `seq2`. The evaluation over candidate windows is done in parallel.
    /// 
    /// Notes on optimizations:
    /// - **Parallelism:** We use Rayon to evaluate candidate windows concurrently.
    /// - **Fixed window size:** The window is fixed to the length of `seq1`, with a factor of resolution differences.
    fn compare_sliding_window(&self, user: &MIDITrack, song_track: &MIDITrack) -> (f64, f64) {
        let query_len = user.notes.len();
        let window_len = (user.notes.len() as f64 * (user.resolution / song_track.resolution) + 1.0) as usize;
        let ref_len = song_track.notes.len();
        if query_len == 0 || ref_len <= query_len {
            return (f64::INFINITY, f64::INFINITY);
        }

        (0..=ref_len - window_len)
            .into_par_iter()
            .map(|start| {
                let candidate_window_notes = &song_track.notes[start..start + window_len];
                let len =  (window_len) as f64;
                if len.is_nan(){
                    println!("[RUST] Length is invalid")
                }
                if len == 0.0f64{
                    println!("[RUST] Length is zero")
                }
                let note_dist = dtw_with_threshold(&user.notes, candidate_window_notes) / len;
                
                let candidate_window_times = &song_track.times[start..start + window_len];
                let time_dist = dtw_with_threshold(&user.times, candidate_window_times) / len;

                let candidate_window_dirs = &song_track.directions[start..start + window_len - 1];
                let dir_dist = dtw_with_threshold(&user.directions, candidate_window_dirs) / len;
                if note_dist.is_nan() || time_dist.is_nan() || dir_dist.is_nan(){
                    println!("[RUST] Error in distance calculation")
                }

                // Apply custom weighting
                let weighted_note = weigh_distance(note_dist, &self.param_types["notes"]);
                let weighted_time = weigh_distance(time_dist, &self.param_types["timings"]);
                let weighted_dir = weigh_distance(dir_dist, &self.param_types["directions"]);

                let total = (weighted_dir * self.param_types["directions"].w
                    + weighted_note * self.param_types["notes"].w
                    + weighted_time * self.param_types["timings"].w)
                    / (self.param_types["directions"].w
                    + self.param_types["notes"].w
                    + self.param_types["timings"].w);

                // Match the start time (e.g., sum of all previous durations)
                let matched_time: f64 = song_track.times[..start].iter().sum();

                (total, matched_time)
            })
            .reduce(|| (f64::INFINITY, f64::INFINITY), |a, b| if a.0 <= b.0 { a } else { b })
    }

    fn compare_full_sequence(&self, user: &MIDITrack, song_track: &MIDITrack) -> (f64, f64) {
        let note_dist = dtw_with_threshold(&user.notes, &song_track.notes);
        let time_dist = dtw_with_threshold(&user.times, &song_track.times);
        let dir_dist = dtw_with_threshold(&user.directions, &song_track.directions);
    
        let weighted_note = weigh_distance(note_dist, &self.param_types["notes"]);
        let weighted_time = weigh_distance(time_dist, &self.param_types["timings"]);
        let weighted_dir = weigh_distance(dir_dist, &self.param_types["directions"]);
    
        let total = (weighted_dir * self.param_types["directions"].w
            + weighted_note * self.param_types["notes"].w
            + weighted_time * self.param_types["timings"].w)
            / (self.param_types["directions"].w
            + self.param_types["notes"].w
            + self.param_types["timings"].w);
    
        (total, 0.0f64)
    }
}

/// Compute the DTW distance between two sequences with early abandonment.
/// If the accumulated cost exceeds `threshold`, the computation aborts early.
/// Upd: due to custom distance weighing and combining, threshold functionality turned out to be unimplementable, deleted the feature
fn dtw_with_threshold(seq1: &[f64], seq2: &[f64]) -> f64 {
    let n = seq1.len();
    let m = seq2.len();
    if n == 0 || m == 0 {
        return f64::INFINITY;
    }

    let band = ((m as f64) * 0.2).floor() as usize;
    let mut prev_row = vec![f64::INFINITY; m + 1];
    let mut curr_row = vec![f64::INFINITY; m + 1];
    prev_row[0] = 0.0;

    for i in 1..=n {
        curr_row[0] = f64::INFINITY;

        let j_start = i.saturating_sub(band).max(1);
        let j_end = (i + band).min(m);

        for j in j_start..=j_end {
            let cost = (seq1[i - 1] - seq2[j - 1]).abs();
            let min_prev = prev_row[j]
                .min(curr_row[j - 1])
                .min(prev_row[j - 1]);
            curr_row[j] = cost + min_prev;
        }

        std::mem::swap(&mut prev_row, &mut curr_row);
    }

    prev_row[m]
}

#[pyfunction]
fn weigh_distance(dist: f64, consts: &Params) -> f64 {
    let exp_2dist = wasc::E.powf(2.0 * (-consts.x0));
    let main_factor = consts.a.powf(1.0 + (dist - consts.x0) / consts.s);
    let first_correcting_factor = 1.0 / (1.0 + consts.b.powf((consts.x0 - dist) / consts.s));
    let second_correcting_factor = 2.0 / (1.0 + wasc::E.powf(2.0 * (-dist))) - 1.0;
    let third_correcting_factor = 2.0 * consts.y0 * (1.0 + exp_2dist) / 
                                (1.0 - exp_2dist);

    main_factor * first_correcting_factor * second_correcting_factor * third_correcting_factor
}



#[pymodule]
fn rust_code(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MidiDTW>()?;
    m.add_class::<MIDITrack>()?;
    Ok(())
}