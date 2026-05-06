import { strict as assert } from "node:assert";
import { petProfile, records } from "./mock-data";
import {
  getHospitalConnectSummary,
  getNearbyAnimalHospitals,
  getSharedCareSummary,
  getShoppingRecommendations,
} from "./expansion-features";

const sharedCare = getSharedCareSummary(petProfile, records);
assert.equal(sharedCare.members.length, 2);
assert.equal(sharedCare.roleOptions.length, 3);
assert.ok(sharedCare.activityItems[0].includes("코코"));
assert.ok(sharedCare.notificationSharingDetail.includes("주의"));

const hospitalSummary = getHospitalConnectSummary(petProfile, records, "어제부터 현관 앞에서 오래 기다림");
assert.equal(hospitalSummary.warningRecords.length, 3);
assert.ok(hospitalSummary.reportPreview.some((item) => item.includes("말티즈")));
assert.ok(hospitalSummary.reportPreview.some((item) => item.includes("어제부터 현관 앞에서 오래 기다림")));
assert.ok(hospitalSummary.shareNotice.includes("전송 API"));

const nearbyHospitals = getNearbyAnimalHospitals(true);
assert.equal(nearbyHospitals.length, 4);
assert.equal(nearbyHospitals[0].distanceLabel, "450m");
assert.ok(nearbyHospitals.every((hospital) => hospital.mapPosition.x >= 0 && hospital.mapPosition.x <= 100));
assert.ok(nearbyHospitals.every((hospital) => hospital.mapCoordinate.lat >= 33 && hospital.mapCoordinate.lat <= 39));
assert.ok(nearbyHospitals.every((hospital) => hospital.mapCoordinate.lng >= 124 && hospital.mapCoordinate.lng <= 132));
assert.ok(nearbyHospitals.some((hospital) => hospital.tags.includes("야간 상담")));

const defaultHospitals = getNearbyAnimalHospitals(false);
assert.ok(defaultHospitals.every((hospital) => hospital.distanceLabel.includes("예상")));

const shopping = getShoppingRecommendations(petProfile, records);
assert.equal(shopping.length, 4);
assert.equal(shopping[0].category, "사료");
assert.ok(shopping.some((item) => item.reason.includes("닭고기")));
