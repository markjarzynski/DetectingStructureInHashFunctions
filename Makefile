CXX :=g++
MPICXX :=mpicxx
CXXFLAGS := -Wall -Wextra
TARGET := structure-in-hash-functions

DEBUG_FLAGS := -g -O0 -DDEBUG
RELEASE_FLAGS := -O3 -DNDEBUG

SRC := fft-test.cpp
OBJ := $(SRC:.cpp=.o)

all: structure-in-hash-functions rng2img rng2noise fft-test structure-in-hash-functions-reference

structure-in-hash-functions: structure-in-hash-functions.cpp include/*.h
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -I include -o structure-in-hash-functions structure-in-hash-functions.cpp

rng2img: rng2img.cpp include/*.h
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -I include -o rng2img rng2img.cpp

rng2noise: rng2noise.cpp include/*.h
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -I include -o rng2noise rng2noise.cpp

fft-test: fft-test.cpp include/*.h
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -I include -o fft-test fft-test.cpp -lfftw3 -lm

structure-in-hash-functions-reference: structure-in-hash-functions-reference.cpp include/*.h
	$(CXX) $(CXXFLAGS) $(RELEASE_FLAGS) -I include -o structure-in-hash-functions-reference structure-in-hash-functions-reference.cpp
	
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

quicktest:
	for i in city esgtsa_linear2 esgtsa_nested2 iqint1_linear2 iqint1_nested2 iqint2 iqint3 jkiss32_linear2 jkiss32_nested2 lcg_linear2 lcg_nested2 md5 murmur3 pcg3d.z pcg4d.w ranlim32_linear2 ranlim32_nested2 superfast_2 tea2.y tea3.y tea4.y tea5.y wang_linear2 wang_nested2 xorshift128 xorshift32_linear2 xorshift32_nested2 xxhash32_2 hybridtaus "-f /dev/random"; \
    do \
        ./structure-in-noise -r -w 32 -h 32 -i 3 -j 3 $$i; \
    done

testdevrandom:
	./structure-in-noise -w 128 -h 128 -i 3 -j 3 -f devrandom

.PHONY: convert archive clean clobber
convert:
	for i in $(wildcard *.ppm) ; \
	do \
		convert $$i $$(basename $$i .ppm).png ; \
	done

archive:
	mkdir -p results
	mv *.png results

clean:
	rm -rf *.ppm *.png

clobber: clean
	rm -rf structure-in-hash-functions structure-in-hash-functions-reference rng2img rng2noise fft-test
