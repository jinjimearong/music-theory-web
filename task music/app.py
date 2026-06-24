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

# [추가됨] 심화 과정(다양한 코드 알아보기) 라우터
@app.route('/chords')
def chords():
    return render_template('chords.html')

@app.route('/analyze_chord', methods=['POST'])
def analyze_chord():
    data = request.json
    notes = data.get('notes', [])
    
    if not notes: 
        return jsonify({"primary": "-", "alternatives": []})
    if len(notes) == 1: 
        return jsonify({"primary": notes[0][:-1], "alternatives": []})
        
    try:
        c = chord.Chord(notes)
        
        # 재즈 표기법으로 변환하는 내부 함수
        def to_jazz_notation(sym):
            if sym == 'Chord Symbol Cannot Be Identified': return "Unknown"
            sym = sym.replace('maj7', 'Δ7').replace('major', 'Δ')
            sym = sym.replace('dim7', '°7').replace('dim', '°')
            sym = sym.replace('m7b5', 'ø7') # 하프 디미니쉬
            sym = sym.replace('aug', '+')
            return sym

        primary_sym = harmony.chordSymbolFigureFromChord(c)
        primary_jazz = to_jazz_notation(primary_sym)
        
        alternatives = set()
        if primary_jazz != "Unknown":
            # 입력받은 모든 음을 한 번씩 가장 아래(Bass)로 강제 배치하여 다른 해석을 찾음
            # (예: C E G A -> C6 인 동시에 Am7/C 로도 해석됨)
            for p in c.pitches:
                test_notes = [n.nameWithOctave for n in c.pitches if n.name != p.name]
                test_notes.append(p.name + '2') # 현재 음을 2옥타브(베이스)로 내림
                
                test_c = chord.Chord(test_notes)
                alt_sym = harmony.chordSymbolFigureFromChord(test_c)
                alt_jazz = to_jazz_notation(alt_sym)
                
                # 디미니쉬 7th 같은 대칭 화음의 다른 이름(Eb°7 등)을 잡아냄
                if alt_jazz != "Unknown" and alt_jazz != primary_jazz:
                    # 슬래시 코드의 베이스 표기를 제거하여 본질적인 코드 이름만 추출
                    clean_alt = alt_jazz.split('/')[0]
                    if clean_alt != primary_jazz.split('/')[0]:
                        alternatives.add(clean_alt)

        return jsonify({
            "primary": primary_jazz, 
            "alternatives": list(alternatives)
        })
    except Exception:
        return jsonify({"primary": "Error", "alternatives": []})

@app.route('/get_scale', methods=['GET'])
def get_scale():
    root_note = request.args.get('root', 'C')
    scale_type = request.args.get('type', 'major')
    try:
        sc = scale.MajorScale(root_note) if scale_type == 'major' else scale.MinorScale(root_note)
        pitches = sc.getPitches(root_note + '4', root_note + '5')
        notes = []
        for p in pitches:
            if '-' in p.name: p = p.getEnharmonic()
            notes.append(p.nameWithOctave)
        return jsonify({"notes": notes})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/get_chord_notes', methods=['GET'])
def get_chord_notes():
    root_note = request.args.get('root', 'C')
    chord_type = request.args.get('type', 'major')
    try:
        root_pitch = pitch.Pitch(root_note + '4')
        
        # [수정됨] 7th, 디미니쉬, 서스, 어그먼티드 등 모든 종류의 인터벌 수학적 계산 추가
        if chord_type == 'major': c = chord.Chord([root_pitch, root_pitch.transpose('M3'), root_pitch.transpose('P5')])
        elif chord_type == 'minor': c = chord.Chord([root_pitch, root_pitch.transpose('m3'), root_pitch.transpose('P5')])
        elif chord_type == 'maj7': c = chord.Chord([root_pitch, root_pitch.transpose('M3'), root_pitch.transpose('P5'), root_pitch.transpose('M7')])
        elif chord_type == 'dom7': c = chord.Chord([root_pitch, root_pitch.transpose('M3'), root_pitch.transpose('P5'), root_pitch.transpose('m7')])
        elif chord_type == 'dim': c = chord.Chord([root_pitch, root_pitch.transpose('m3'), root_pitch.transpose('d5')])
        elif chord_type == 'dim7': c = chord.Chord([root_pitch, root_pitch.transpose('m3'), root_pitch.transpose('d5'), root_pitch.transpose('d7')])
        elif chord_type == 'sus4': c = chord.Chord([root_pitch, root_pitch.transpose('P4'), root_pitch.transpose('P5')])
        elif chord_type == 'aug': c = chord.Chord([root_pitch, root_pitch.transpose('M3'), root_pitch.transpose('A5')])
        else: c = chord.Chord([root_pitch, root_pitch.transpose('M3'), root_pitch.transpose('P5')])
            
        notes = []
        for p in c.pitches:
            if '-' in p.name: p = p.getEnharmonic()
            notes.append(p.nameWithOctave)
        return jsonify({"notes": notes})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
