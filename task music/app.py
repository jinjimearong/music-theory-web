from flask import Flask, render_template, request, jsonify
from music21 import chord, harmony, scale, pitch

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/play')
def play():
    return render_template('play.html')

@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/analyze_chord', methods=['POST'])
def analyze_chord():
    data = request.json
    notes = data.get('notes', [])
    if not notes: return jsonify({"chord": "-"})
    if len(notes) == 1: return jsonify({"chord": notes[0][:-1]})
        
    try:
        c = chord.Chord(notes)
        chord_symbol = harmony.chordSymbolFigureFromChord(c)
        if chord_symbol == 'Chord Symbol Cannot Be Identified': return jsonify({"chord": "Unknown"})
        return jsonify({"chord": chord_symbol})
    except Exception:
        return jsonify({"chord": "Error"})

# [수정됨] 마이너 스케일의 플랫(-) 기호를 DOM이 인식하는 샵(#)으로 변환
@app.route('/get_scale', methods=['GET'])
def get_scale():
    root_note = request.args.get('root', 'C')
    scale_type = request.args.get('type', 'major')
    
    try:
        if scale_type == 'major':
            sc = scale.MajorScale(root_note)
        else:
            sc = scale.MinorScale(root_note)
            
        pitches = sc.getPitches(root_note + '4', root_note + '5')
        notes = []
        for p in pitches:
            # music21은 플랫을 '-'로 반환하므로 화면 표시를 위해 이명동음(샵)으로 변환
            if '-' in p.name:
                p = p.getEnharmonic()
            notes.append(p.nameWithOctave)
            
        return jsonify({"notes": notes})
    except Exception as e:
        return jsonify({"error": str(e)})

# [수정됨] 텍스트 파싱 대신 기준음(Root)으로부터 정확한 음정(Interval) 간격을 더해 화음 도출
@app.route('/get_chord_notes', methods=['GET'])
def get_chord_notes():
    root_note = request.args.get('root', 'C')
    chord_type = request.args.get('type', 'major')
    
    try:
        root_pitch = pitch.Pitch(root_note + '4')
        
        # 1-3-5도 화음(Triad) 구성음을 수학적으로 더해서 계산
        if chord_type == 'major':
            # 장3도(M3), 완전5도(P5) 위
            c = chord.Chord([root_pitch, root_pitch.transpose('M3'), root_pitch.transpose('P5')])
        else:
            # 단3도(m3), 완전5도(P5) 위
            c = chord.Chord([root_pitch, root_pitch.transpose('m3'), root_pitch.transpose('P5')])
            
        notes = []
        for p in c.pitches:
            if '-' in p.name:
                p = p.getEnharmonic()
            notes.append(p.nameWithOctave)
            
        return jsonify({"notes": notes})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)