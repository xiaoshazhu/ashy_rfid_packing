function chooseTemp(id) {
  $("#" + id).click();
}

$("#tmplFileSrc").on("change", function (e) {
  var file = e.target.files[0];
  console.log(file);
  $("#tempDisplay").val(file.name);
});

//文件转base64
function fileToBase64(file) {
  return new Promise(function (resolve, reject) {
    var reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = function () {
      var base64 = reader.result.split(",")[1];
      resolve(base64);
    };
  });
}

// 获取日期
function getDateTime(date) {
  if (date) {
    const time = {
      yyyy: date.getFullYear(),
      MM: date.getMonth() + 1,
      dd: date.getDate(),
      hh: date.getHours(),
      mm: date.getMinutes(),
      ss: date.getSeconds(),
      hm: Date.now(),
      w: ["Sun", "Mon", "Tues", "Wed", "Thurs", "Fri", "Sat"][date.getDay()],
    };
    let format = "yyyy-MM-dd hh:mm:ss:hm";
    for (const temp in time) {
      format = format.replace(
        temp,
        (Array(temp.length).join("0") + time[temp]).slice(-temp.length)
      );
    }
    return format;
  }
}

//添加日志信息
function creatLog(text) {
  $(".terminal").append(`<div>${getDateTime(new Date())}：${text}</div>`);
  //滚动到最底部
  $(".terminal").animate({ scrollTop: "10000px" }, 50);
}
//生成成功请求的模板日志
function creatSucessLog(api, funcName, res) {
  let log = res.outParams
    ? `${api}(${funcName}) successful, Message: ${JSON.stringify(res.outParams)}`
    : `${api}(${funcName}) successful `;
  creatLog(log);
}

//生成失败请求的模板日志
function creatErrLog(api, funcName, res) {
  let log = `${api}(${funcName}) failed, Message: ${res.rsltMsg}`;
  creatLog(log);
}
//清空日志
function clearLog() {
  $(".terminal").empty();
}
// 开启提示框
function openMask(content, autoClose) {
  var text = content;
  $(".popup_tips_content").text(text);
  $(".popup_tips").fadeIn();
  $("body").css("overflow", "hidden");
  if (autoClose) {
    setTimeout(function () {
      // $('.DC8600_popup_tips').fadeOut()
      closeMask();
    }, 3000);
  }
}

// 关闭提示框
function closeMask() {
  $(".popup_tips").fadeOut();
  $("body").css("overflow", "auto");
}

//重置信息
function reset() {
  $("input").val("");
  $("input[type='checkbox']").prop("checked", false);
  $("input[type='radio']").prop("checked", false);
  $("#printCount").val("1");
}

//发送GET请求
function sendGetRequest(url, callback) {
  $.ajax({
    url: url,
    type: "GET",
    success: function (data) {
      callback(data);
    },
    error: function (xhr, status, error) {
      openMask("Request failure");
    },
  });
}

//发送POST请求
function sendPostRequest(funcId, funcName, data, callback) {
  return new Promise((resolve, reject) => {
    $.ajax({
      url: "http://127.0.0.1:9001/",
      method: "post",
      timeout: 30000,
      data: JSON.stringify({
        version: "1.0",
        seqNo: generateUniqueId(),
        funcName: funcId,
        inParams: data,
      }),
      success: function (response) {
        if (response.rtnCode == "0") {
          resolve(response.outParams);
          creatSucessLog(funcId, funcName, response);
        } else {
          reject(response.rsltMsg);
          creatErrLog(funcId, funcName, response);
        }
      },
      error: function (xhr, status, error) {
        console.error("An error occurred:", status, error);
        reject(error);
      },
    });
  });
}

//生成唯一序列号
function generateUniqueId() {
  var timestamp = Date.now().toString(36); // 使用36进制，避免出现数字开头的问题
  var randomNum = Math.random().toString(36).substr(2, 9); // 获取随机数的36进制表示，并截取后9位
  return timestamp + randomNum;
}

// 字转换成符串类型的浮点数
function toFloatString(data) {
  var float = parseFloat(data) || 0;
  return float.toFixed(2);
}
// 字转换成符串类型的整数
function toIntString(data) {
  var int = parseInt(data) || 0;
  return int.toString();
}

function getAllStatus(mainStatus, warnStatus, errStatus)
{
  let mainStatusGroup = [
    "Device idle",
    "Device busy",
    "Cache is not empty",
    "Cache is empty",
    "The panel is in the set state",
    "Label reading and writing completed",
    "The retry and invalidation process is in progress",
    "The make-up printing process is in progress",
    "RFID automatic verification in progress",
    "RFID custom command in progress",
    "No RFID module"
  ]
  let warnStatusGroup = [
   "Paper is about to run out"
  ]
  let errStatusGroup = [
    "Label or black label positioning error",
    "Paper jam",
    "Paper tearing error",
    "Lack of paper",
    "Knife error",
    "Paper loading error",
    "Carbon tape error",
    "Lifting the print head",
    "Printing head overheating",
    "EPC data missing in print data",
    "RFID re printing failed",
    "RFID calibration failed",
    "RFID error",
    "Pause or offline"
  ]
  let mainStatusArr = mainStatus.split(",");
  let warnStatusArr = warnStatus.split(",");
  let errStatusArr = errStatus.split(",");

  let rtnStr = "Main status: ";
  for (let i = 0; i < mainStatusArr.length; i++) {
    let idx = mainStatusArr[i] - 1;
    rtnStr += mainStatusGroup[idx];
    rtnStr += "; ";
  }

  if (warnStatus && warnStatusArr.length > 0) {
    rtnStr += " Warn status: ";
    for (let i = 0; i < warnStatusArr.length; i++) {
      let idx = warnStatusArr[i] - 1;
      rtnStr += warnStatusGroup[idx];
      rtnStr += "; ";
    }  
  }
  
  if (errStatus && errStatusArr.length > 0) {
    rtnStr += " Error status: ";
    for (let i = 0; i < errStatusArr.length; i++) {
      let idx = errStatusArr[i] - 1;
      rtnStr += errStatusGroup[idx];
      rtnStr += "; ";
    }  
  }  

  return rtnStr;
}
