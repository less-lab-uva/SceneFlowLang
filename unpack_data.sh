if test -d "./study_data/" ; then
  printf "Data has already been unpacked to ./study_data/, skipping.\n"
else
  printf "Unpacking study_data.7z to ./study_data/. Will result in ~1.1GB.\n"
  7z x study_data.7z -o./
  printf "Also creating conda environments.\n"
  conda env create -f tcp_environment.yml
  conda env create -f lav_environment.yml
  source install_mona.sh
fi
if test -d "./study_timing_data/" ; then
  printf "Timing data has already been unpacked to ./study_timing_data/, skipping.\n"
else
  printf "Unpacking study_timing_data.7z to ./study_timing_data/. Will result in ~110MB.\n"
  7z x study_timing_data.7z -o./
fi