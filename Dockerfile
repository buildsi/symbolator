FROM ghcr.io/autamus/clingo:latest
# docker build -t symbolator .
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl
RUN /bin/bash -c "curl -L https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh > miniconda.sh && \
    bash miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh"
ENV PATH /opt/conda/envs/clingo-env/bin:${PATH}
ENV PATH=/opt/conda/bin:$PATH
WORKDIR /code
ADD . /code
RUN python setup.py install
ENTRYPOINT /bin/bash
