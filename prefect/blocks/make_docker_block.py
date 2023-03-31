from prefect.infrastructure.docker import DockerContainer

# alternative to creating DockerContainer block in the UI
docker_block = DockerContainer(
    image="mbertrand/prefect:eo_climate",  # insert your image here
    image_pull_policy="ALWAYS",
    auto_remove=True,
)

docker_block.save("docker_eo", overwrite=True)
