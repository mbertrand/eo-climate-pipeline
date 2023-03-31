from prefect.filesystems import GitHub

block = GitHub(
    repository="https://github.com/mbertrand/eo-climate-pipeline.git"
)
block.save("eo-climate-github")