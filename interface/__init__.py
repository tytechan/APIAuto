#encoding = utf - 8


Environment_Select = \
{
    "200": "http://cdwpdev01.chinacloudapp.cn:9200",
    "500": "http://kintergration.chinacloudapp.cn:9002",
    "400": "http://cdwpdev01.chinacloudapp.cn:9400",
    "450": "http://cdwpdev01.chinacloudapp.cn:9003",
    "510": "http://kintergration01.chinacloudapp.cn:9510",
    "520": "http://kintergration01.chinacloudapp.cn:9520",
    "530": "http://kintergration01.chinacloudapp.cn:9530",
    "540": "http://kintergration01.chinacloudapp.cn:9540",
    "600": "http://kintergration.chinacloudapp.cn:9003",
    "700": "http://kdevelop.chinacloudapp.cn:9003",
    "800": "http://cdwp.cnbmxinyun.com",
    "810": "http://pre-mongodb-01.chinacloudapp.cn:9003"
}


Function_Select = {
    "销售合同": "/contract",
    # 作废与新建仅detail接口不同
    "销售合同作废": "/contract",
    "采购合同": "/purchase-contract",
    "采购确认单": "/purchase_confirm",
    "采购订单": "/poheader",
    "采购申请": "/poheader",
    "借出单": "/productlend",
    "放货单": "/productout",
    "付款申请单": "/credit",
    "报销单": "/reimburse",
    "费用申请单": "/interiorbills",
    "开票申请": "/mkinvoicenew",
}


specialUser = {
    "张鑫": "zhangxin01",
    "王洋": "wangyang01",
}

# 审批流处理专用
params_dict = {
    "mydoing_dict": {
        "销售合同": {
            "limit": 500,
            "orderby": {},
            "page": 1,
            "processtype": [
                "CONT",
                "CONT_CHANGE",
                "CONT_CONTENTCHANGE",
                "COGN",
                "COGN_CHANGE",
                "COGN_CONTENTCHANGE",
                "SERVICE_CONT",
                "SERVICE_CONT_CHANGE",
                "CONT_CANCEL",
                "COGNCONT_CANCEL"
            ],
            "querys": {
                "groupno": ""
            }
        },
        "销售合同作废": {
            "limit": 500,
            "orderby": {},
            "page": 1,
            "processtype": [
                "CONT",
                "CONT_CHANGE",
                "CONT_CONTENTCHANGE",
                "COGN",
                "COGN_CHANGE",
                "COGN_CONTENTCHANGE",
                "SERVICE_CONT",
                "SERVICE_CONT_CHANGE",
                "CONT_CANCEL",
                "COGNCONT_CANCEL"
            ],
            "querys": {
                "groupno": ""
            }
        },
        "采购合同": {
            "limit": 500,
            "orderby": {},
            "page": 1,
            "processtype": [
                "CGHT",
                "CGHT_CHANGE",
                "CGHT_CANCEL"
            ],
            "querys": {
                "fullcode": ""
            }
        },
        "采购确认单": {
            "limit": "10",
            "page": 1,
            "processtype": [
                "CGQRD",
                "CGQRD_TQXD",
                "CGQRD_CHANGE",
                "CGQRD_CANCEL"
            ],
            "querys": {
                "code": "",
                "curreceiver": "",
                "ownername": ""
            }
        },
        "采购订单": {
            "limit": 500,
            "orderby": {},
            "page": 1,
            "processtype": [
                "ZD02",
                "ZD12",
                "ZD14"
            ],
            "querys": {
                "EBELN": ""
            }
        },
        "借出单": {
            "limit": "10",
            "page": 1,
            "processtype": [
                "JCD",
                "JCDRN",
                "JCDRT"
            ],
            "querys": {
                "client_name": "",
                "code": "",
                "lastactiveuname": "",
                "user_name": ""
            }
        },
        "放货单": {
            "limit": "10",
            "page": 1,
            "processtype": [
                "FHSQ"
            ],
            "querys": {
                "client": "",
                "code": "",
                "fhcode": "",
                "lastactiveuname": "",
                "sale": "",
                "sapcode": ""
            }
        },
        "付款申请单": {
            "limit": 500,
            "orderby": {},
            "page": 1,
            "processtype": [
                "FKSQ",
                "HBFK",
                "FKZF",
                "FKBG"
            ],
            "querys": {
                "ZSQNO": ""
            }
        },
        "报销单": {
            "limit": "10",
            "page": 1,
            "processtype": [
                "BXD",
                "BXDCANCEL"
            ],
            "querys": {
                "code": "",
                "costtype": "",
                "lastactiveuname": "",
                "orgname": "",
                "username": ""
            }
        },
        "费用申请单": {
            "limit": "10",
            "page": 1,
            "processtype": [
                "NBDD",
                "NBDDZF"
            ],
            "querys": {
                "USER0": "",
                "ZINORD": "",
                "ZSQNR": "",
                "lastactiveuname": ""
            }
        },
        "开票申请": {
            "page": 1,
            "limit": "10",
            "processtype": [
                "KPSQN"
            ],
            "querys": {
                "kptype": "",
                "ZFPLX": "",
                "XBLNR": "",
                "contracttype": ""
            }
        },
    },
    "mydoing_key": {
        "销售合同": "querys.groupno",
        "销售合同作废": "querys.groupno",
        "采购合同": "querys.fullcode",
        "采购确认单": "querys.code",
        "采购订单": "querys.EBELN",
        "借出单": "querys.code",
        "放货单": "querys.fhcode",
        "付款申请单": "querys.ZSQNO",
        "报销单": "querys.code",
        "费用申请单": "querys.ZINORD",
        "开票申请": "querys.XBLNR",
    },
    "list_unfinished": {
        "销售合同": {
            "approval_status": "2",
            "contractno": "",
            "contracttype": "",
            "corp": "",
            "limit": "10",
            "page": 1,
            "project": "",
            "receipttype": "",
            "salesname": "",
            "salesorderid": "",
            "status": "",
            "stomer": "",
            "supplierorderno": "",
            "type": "CONT"
        },
        "销售合同作废": {
            "approval_status": "2",
            "contractno": "",
            "contracttype": "",
            "corp": "",
            "limit": "10",
            "page": 1,
            "project": "",
            "receipttype": "",
            "salesname": "",
            "salesorderid": "",
            "status": "",
            "stomer": "",
            "supplierorderno": "",
            "type": "CONT"
        },
        "采购合同": {
            "choice": {
                "creator": "",
                "fullcode": "",
                "project_name": "",
                "purchaser": {
                    "vendee": ""
                },
                "sap_code": "",
                "status": "2",
                "supplier_name": "",
                "supplier_order": "",
                "type": ""
            },
            "fields": [],
            "limit": "10",
            "order": "",
            "page": 1
        },
        "采购确认单": {
            "approval_status": "1",
            "code": "",
            "doc_status": "",
            "limit": "10",
            "page": 1,
            "sales_name": ""
        },
        "采购订单": {
            "BSART": "",
            "EBELN": "",
            "EKORG": "",
            "ERNAM": "",
            "NAME": "",
            "ZZPO": "",
            "approval_status": "2",
            "limit": "20",
            "page": 1
        },
        "借出单": {
            "approval_status": "2",
            "clientname": "",
            "close_status": "",
            "code": "",
            "corp": "",
            "delivery_status": "",
            "expire_status": "",
            "limit": "10",
            "loan_status": "",
            "page": 1,
            "productline": "",
            "project_title": "",
            "username": ""
        },
        "放货单": {
            "approval_status": "2",
            "client": "",
            "code": "",
            "corp": "",
            "create_time": "",
            "creator": "",
            "department": "",
            "fromdate": "",
            "limit": "10",
            "orderno": "",
            "page": 1,
            "sale": "",
            "sapcode": "",
            "todate": ""
        },
        "付款申请单": {
            "AUFUSER0": "",
            "EBELN": "",
            "LOEVM": "",
            "PRCTR": "",
            "ZBM": "",
            "ZCGSW": "",
            "ZFKFS": "",
            "ZFKSTA": "",
            "ZFKZL": "",
            "ZFKZT": "",
            "ZPRINTX": "",
            "ZSJDAT": "",
            "ZSKDW": "",
            "ZSQNO": "",
            "approval_status": "2",
            "limit": "10",
            "page": 1
        },
        "报销单": {
            "approval_status": "2",
            "code": "",
            "costtype": "",
            "limit": "10",
            "page": 1,
            "profit_center": "",
            "usercode": "",
            "username": ""
        },
        "费用申请单": {
            "BUKRS": "",
            "PRCTR": "",
            "USER0": "",
            "USER5": "",
            "ZINORD": "",
            "ZZSYB": "",
            "approval_status": "2",
            "limit": "10",
            "page": 1
        },
        "开票申请": {
            "BUKRS": "",
            "XBLNR": "",
            "ZFPLX": "",
            "approval_status": "2",
            "contractno": "",
            "cusname": "",
            "dateEnd": "",
            "dateStar": "",
            "invoiceamount": "",
            "limit": "10",
            "page": 1,
            "printed": "",
            "statusofrecbill": "",
            "tradername": "",
            "user": ""
        },
    },
    "list_done": {
        "销售合同": {
            "approval_status": "1",
            "contractno": "",
            "contracttype": "",
            "corp": "",
            "limit": "10",
            "page": 1,
            "project": "",
            "receipttype": "",
            "salesname": "",
            "salesorderid": "",
            "status": "v",
            "stomer": "",
            "supplierorderno": "",
            "type": "CONT"
        },
        "销售合同作废": {
            "approval_status": "1",
            "contractno": "",
            "contracttype": "",
            "corp": "",
            "limit": "10",
            "page": 1,
            "project": "",
            "receipttype": "",
            "salesname": "",
            "salesorderid": "",
            "status": "c",
            "stomer": "",
            "supplierorderno": "",
            "type": "CONT"
        },
        "采购合同": {
            "choice": {
                "creator": "",
                "fullcode": "",
                "project_name": "",
                "purchaser": {
                    "vendee": ""
                },
                "sap_code": "",
                "status": "1",
                "supplier_name": "",
                "supplier_order": "",
                "type": ""
            },
            "fields": [],
            "limit": "10",
            "order": "",
            "page": 1
        },
        "采购确认单": {
            "approval_status": "2",
            "code": "",
            "doc_status": "",
            "limit": "10",
            "page": 1,
            "sales_name": ""
        },
        "采购订单": {
            "BSART": "",
            "EBELN": "",
            "EKORG": "",
            "ERNAM": "",
            "NAME": "",
            "ZZPO": "",
            "approval_status": "1",
            "limit": "20",
            "page": 1
        },
        "借出单": {
            "approval_status": "1",
            "clientname": "",
            "close_status": "",
            "code": "",
            "corp": "",
            "delivery_status": "",
            "expire_status": "",
            "limit": "10",
            "loan_status": "",
            "page": 1,
            "productline": "",
            "project_title": "",
            "username": ""
        },
        "放货单": {
            "approval_status": "1",
            "client": "",
            "code": "",
            "corp": "",
            "create_time": "",
            "creator": "",
            "department": "",
            "fromdate": "",
            "limit": "10",
            "orderno": "",
            "page": 1,
            "sale": "",
            "sapcode": "",
            "todate": ""
        },
        "付款申请单": {
            "AUFUSER0": "",
            "EBELN": "",
            "HAS_HB": "",
            "LOEVM": "",
            "PRCTR": "",
            "ZBM": "",
            "ZCGSW": "",
            "ZFKFS": "",
            "ZFKSTA": "",
            "ZFKZL": "",
            "ZFKZT": "",
            "ZPRINTX": "",
            "ZSJDAT": "",
            "ZSKDW": "",
            "ZSQNO": "",
            "approval_status": "1",
            "limit": "10",
            "page": 1
        },
        "报销单": {
            "approval_status": "1",
            "certcode": "",
            "code": "",
            "costtype": "",
            "finenddate": "",
            "finfromdate": "",
            "invoicetypestr": "",
            "limit": "10",
            "page": 1,
            "profit_center": "",
            "status": "valid",
            "usercode": "",
            "username": ""
        },
        "费用申请单": {
            "BUKRS": "",
            "PRCTR": "",
            "USER0": "",
            "USER5": "",
            "ZINORD": "",
            "ZZSYB": "",
            "approval_status": "1",
            "limit": "10",
            "page": 1
        },
        "开票申请": {
            "BUKRS": "",
            "XBLNR": "",
            "ZFPLX": "",
            "approval_status": "1",
            "contractno": "",
            "cusname": "",
            "dateEnd": "",
            "dateStar": "",
            "invoiceamount": "",
            "limit": "10",
            "page": 1,
            "printed": "0",
            "statusofrecbill": "0",
            "tradername": "",
            "user": ""
        },
    },
    "list_key": {
        "销售合同": "contractno",
        "销售合同作废": "contractno",
        "采购合同": "choice.fullcode",
        "采购确认单": "code",
        "采购订单": "EBELN",
        "借出单": "code",
        "放货单": "code",
        "付款申请单": "ZSQNO",
        "报销单": "code",
        "费用申请单": "ZINORD",
        "开票申请": "XBLNR",
    }
}


