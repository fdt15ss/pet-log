import { strict as assert } from "node:assert";
import test from "node:test";
import axios, { type AxiosAdapter } from "axios";
import { NextRequest } from "next/server";
import { GET } from "../app/api/v1/[...path]/route";
import { restoreEnvValue } from "./sprint-test-utils";

test("pets API는 backend가 빈 목록을 반환하면 더미 pet을 만들지 않고 빈 목록을 유지한다", async () => {
  const previousBaseUrl = process.env.PET_LOG_BACKEND_API_BASE_URL;
  const previousPetId = process.env.PET_LOG_BACKEND_PET_ID;
  const previousAdapter = axios.defaults.adapter;
  process.env.PET_LOG_BACKEND_API_BASE_URL = "http://127.0.0.1:27893";
  process.env.PET_LOG_BACKEND_PET_ID = "pet-local-default";

  axios.defaults.adapter = (async (config) => {
    return {
      config,
      data: {
        success: true,
        data: {
          pets: [],
        },
      },
      headers: {},
      request: {},
      status: 200,
      statusText: "OK",
    };
  }) as AxiosAdapter;

  try {
    const response = await GET(new NextRequest("http://localhost/api/v1/pets") as never, {
      params: Promise.resolve({ path: ["pets"] }),
    });
    const json = await response.json();

    assert.equal(response.status, 200);
    assert.equal(json.ok, true);
    assert.deepEqual(json.data.pets, []);
  } finally {
    axios.defaults.adapter = previousAdapter;
    restoreEnvValue("PET_LOG_BACKEND_API_BASE_URL", previousBaseUrl);
    restoreEnvValue("PET_LOG_BACKEND_PET_ID", previousPetId);
  }
});
