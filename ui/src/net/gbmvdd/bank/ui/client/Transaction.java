package net.gbmvdd.bank.ui.client;

import com.google.gwt.core.client.JavaScriptObject;
import com.google.gwt.json.client.JSONBoolean;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;

public class Transaction extends JavaScriptObject {
	protected Transaction() {
	}
	
	public final native String getEventId() /*-{
		return this.event_id;
	}-*/;

	public final native String getFitId() /*-{
		return this.fitid;
	}-*/;

    public final void setFitId(String fitid) {
      new JSONObject(this).put("isInvoiceable",
          new JSONString(fitid));
    }

	public final native String getDate() /*-{
		return this.date;
	}-*/;
	
	public final native String getName() /*-{
		return this.name;
	}-*/;

	public final native String getMemo() /*-{
		return this.memo;
	}-*/;

	public final native String getAmount() /*-{
		return this.amount;
	}-*/;

    public final native boolean isLikelyInvoiceable() /*-{
        return this.isLikelyInvoiceable;
    }-*/;

    public final native boolean isInvoiceable() /*-{
        return this.isInvoiceable;
    }-*/;

    public final void setIsInvoiceable(boolean invoiceable) {
      new JSONObject(this).put("isInvoiceable",
          JSONBoolean.getInstance(invoiceable));
    }

    public final native boolean isLikelyPayment() /*-{
        return this.isLikelyPayment;
    }-*/;
    
    public final native boolean isPayment() /*-{
        return this.isPayment;
    }-*/;

    public final String toJSON() {
      return new JSONObject(this).toString();
    }
}
