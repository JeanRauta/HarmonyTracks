from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH 

input_audio_path = "./teste.mp3"

output_directory = "./" 

predict_and_save(
    audio_path_list=[input_audio_path], 
    output_directory=output_directory, 
    save_midi=True,  
    sonify_midi=False, 
    save_model_outputs=False, 
    save_notes=False,  
    model_or_model_path=ICASSP_2022_MODEL_PATH 
)