---
title: Discounted Cash Flow Analysis&#58;  Complete Tutorial With Examples
url: https://www.lynalden.com/discounted-cash-flow-analysis/
date: 2017-02-01
---

# Discounted Cash Flow Analysis:  Complete Tutorial With Examples

*Calculating the sum of future discounted cash flows is the gold standard to determine how much an investment is worth.
This guide show you how to use discounted cash flow analysis to determine the fair value of most types of investments, along with several example applications.
You can either start here from the beginning, or jump to the specific section you want:

Discounted cash flows 101: how it works
Business example using discounted cash flows
Project example using discounted cash flows
Bond pricing example using discounted cash flows
A streamlined stock valuation method
Limitations of discounted cash flow analysis

## How to do Discounted Cash Flow (DCF) Analysis

The discounted cash flow method is used by professional investors and analysts at investment banks to determine how much to pay for a business, whether it’s for shares of stock or for buying a whole company.
And it’s also used by financial analysts and project managers in major companies to determine whether a given project will be a good investment, like for a new product launch or a new manufacturing facility.
It’s applicable to any scenario where you are considering paying money now in expectation of receiving more money in the future.
I’ve personally used it both for engineering projects and stock analysis.
Put simply, discounted cash flow analysis rests on the principle that an investment now is worth an amount equal to the sum of all the future cash flows it will produce, with each of those cash flows being discounted to their present value.
Here is the equation:

Let’s break that down.

**DCF** is the sum of all future discounted cash flows that the investment is expected to produce.  This is the fair value that we're solving for.
**CF** is the total cash flow for a given year. CF1 is for the first year, CF2 is for the second year, and so on.
**r** is the discount rate in decimal form. The discount rate is basically the target rate of return that you want on the investment.

And we'll start with an example.  If a trustworthy person offered you $1,500 in three years, and asked how much you're willing to pay for that eventual reward today, how much would you offer?
To answer that question, you need to translate that $1,500 into its value to you today.
For example, if you had $1,000 today, and compounded it at 14.5% per year, it would equal about $1,500 in three years:

Alternatively, if you had $1,200 today, and compounded it at just 7.7% per year, it would equal about $1,500 in three years:

So, the amount that $1,500 three years from now is worth to you today depends on what rate of return you can compound your money at during that period. If you have a target rate of return in mind, you can determine the exact maximum that you should be willing to pay today for the expected return in 3 years.
That’s what the DCF equation does; it translates future cash flows that you will likely receive from an investment into their present value to you today, based on the compounded rate of return you could reasonably achieve with your money today.
When you're buying shares of stock, or a whole business, or real estate, or trying to figure out which project to invest in out of several options, analyzing the expected discounted cash flows can help you decide which investments are worthwhile and which ones are not.
If you find that you can buy an investment for a price that is below the sum of discounted cash flows, you may be looking at an undervalued (and therefore potentially very rewarding!) investment.  On the other hand, if the price is higher than the sum of discounted cash flows that its expected to produce, that's a strong sign that it may be overvalued.
Now let's go over a bunch of example applications.
## How to Determine the Fair Value of a Business

Suppose you were offered a private deal to buy a 20% stake in a local business that has been around for decades, and you know the owner well.
The business has been passed down through three generations and is still going strong with a growth rate of about 3% per year. It currently produces $500,000 per year in free cash flows, so this investment into a 20% stake will likely give you $100,000 per year in cash, and will likely grow at a 3% rate per year.
How much should you pay for that stake?
This year, the business will give you $100,000. Next year, it’ll give you $103,000. The year after that, it’ll give you $106,090. And so on, assuming your growth estimates are accurate.
The stake in the business is worth an amount of money equal to the sum of all future cash flows it’ll produce for you, with each of those cash flows being discounted to their present value.
Since this is a private business deal with low liquidity, let’s say that your target compounded rate of return is 15% per year. If that’s a rate of return you know you can achieve on other investments, you would only want to buy this business stake if you can get it for a low enough price that it’ll give you at least that rate of return. Therefore, 15% becomes the compounded discount rate that you apply to all future cash flows.
So, let’s do the equation:

“DCF” in that equation is the variable we are solving for. That’s the sum of all future discounted cash flows, and is the maximum amount you should pay for the business today if you want to get a 15% annualized return or higher for a long time.
The numerators represent the expected annual cash flows, which in this case start at $100,000 for the first year and then grow by 3% per year forever after.
The denominators convert those annual cash flows into their present value, since we divided them by a compounded 15% annually.
Here’s a table for the first five years, showing that even as the actual expected cash flows will keep growing, the discounted versions of those cash flows will shrink over time, because the discount rate is higher than the growth rate:

You can use Excel or any other spreadsheet program to carry that pattern out indefinitely.  Here’s the chart of the first 25 years:

The dark blue lines represent the actual cash flows that you’ll get each year for the next 25 years, assuming the business grows as expected at 3% per year.  As you go onto infinity, the sum of all the cash flows will also be infinite.
The light blue lines represent the discounted versions of those cash flows.
For example, on year 5 you’re expected to receive $112,551 in actual cash flows, but that would only be worth $55,958 to you today. (Because if you had $55,958 today, and you could grow it by 15% per year for 5 years in a row, you will have turned it into $112,551 after those five years.)
Because the discount rate (15%) that we're applying is much higher than the growth rate of the cash flows (3%), the discounted versions of those future cash flows will shrink and shrink each year, and asymptotically approach zero.
Therefore, although the sum of all future cash flows (dark blue lines) is potentially infinite, the sum of all discounted cash flows (light blue lines) is just $837,286, even if the business lasts forever.
That's the key answer to the original question; $837,286 is the maximum you should pay for the stake in the business, assuming you want to achieve 15% annual returns, and assuming your estimates for growth are accurate.
And the sum of just the first 25 years of discounted cash flows for this example is $784,286. In other words, even if the company went out of business a few decades from now, you’d still get most of the rate of return that you expected. The company doesn't have to last forever for you to get your money's worth.
## How to Value a Project

A lot of businesses use discounted cash flow analysis to determine which projects to invest in. They have a finite amount of money to spend each year, so they want to put it into the projects that are expected to result in the highest rate of return. They don’t just want to throw darts at a dartboard and see what sticks.
Companies usually use their weighted-average cost of capital (WACC) as their discount rate, which takes into account the average rate of return that their stock and bond holders expect.
Suppose you’re a financial analyst at a company, and you are recommending whether the company should invest in Project A or Project B.
Each of the two projects has been proposed by a lead engineer, but the company can only invest in creating one of them this year, and so your manager wants you to give her advice on which one to invest in. Your company’s WACC is 9%, so you’ll use 9% as your discount rate.
Here are the two projects:

Project A starts with an initial investment to make a tech product, followed by a growing income stream, until the product becomes obsolete and is terminated.
Project B starts with an initial investment to make a different product, and makes no sales, but the whole product is expected to be sold in five years to some other company for a large payoff of $14 million.
Which project, assuming both carry the same risk, should the financial analyst recommend to her manager?
First, let’s analyze the discounted cash flows for Project A:

The sum of the discounted cash flows (far right column) is $9,707,166.
Therefore, the net present value (NPV) of this project is $6,707,166 after we subtract the $3 million initial investment.
Now, let’s analyze Project B:

The sum of the discounted cash flows is $9,099,039.
Therefore, the net present value (NPV) of this project is $6,099,039 after we subtract the $3 million initial investment.
We can conclude that from a financial standpoint, Project A is better, since it has a higher net present value.
Even though Project B will bring in $14 million in cash over its lifetime and Project A will only bring in $12 million, Project A is more valuable because of the earlier timing of those expected cash flows.
Thus, you should advise your manager to pick Project A to invest in for this year, if she can only invest in one.
Of course, in the real world, there could still be circumstances that might lead to the manager picking project B instead. There could be non-financial reasons to invest in that project, such as assisting with long-term strategic positioning, or trying to enter a new market, or something of that nature.
But in terms of which project is inherently more profitable assuming the cash flow expectations are accurate, the answer is Project A.
## How to Price Bonds with DCF

Bonds have a large secondary market, and their prices change based on the prevailing interest rates.
The prices of those bonds on the secondary market are determined by discounted cash flow analysis:

**Bond Price** refers to what investors are currently willing to pay for a bond.
The**Coupon** refers to the payments made as part of the bond agreement to the bondholder for each year.
**i** is the interest rate in decimal form. This is the yield to maturity that the bond buyer is targeting.
**Value at Maturity** is the final payment the bondholder gets back at the end, or the "par value" of the bond.

Depending on the frequency of the coupon payments, there are several variants of this formula that can re-organize it into an easier form for the specific type of bond that is being priced.
The point is, at its core, bond pricing follows the same DCF formula as everything else that provides cash flows.
The higher the interest rate "i" for the bonds, the lower the bond price will be, assuming the coupon and value at maturity are unchanged.  This is why when the Federal Reserve raises interest rates, the prices of existing bonds on the secondary market may decrease. Similarly, when the Federal Reserve reduces interest rates, existing bonds may increase in price.
## How to Calculate the Fair Value of a Stock

One of the most common applications of discounted cash flows is for stock analysis. Wall Street analysts delve deep into the books of companies, trying to determine what the future cash flows will be and thus what the stock is worth today.
You can apply the same method that we used for the whole business example. You just have to add an extra step of dividing the answer by the number of existing shares to determine the fair value per share.
Here's a streamlined input model I use for stock analysis, called StockDelver:

Source: StockDelver
It breaks down the growth estimate from top to bottom, starting with volume and pricing, and moving down towards analyzing the growth of earnings per share (EPS). You can easily substitute free cash flow (FCF) for EPS if you want.
A common principle in engineering is that you solve a hard problem by breaking it into little pieces and solving those little pieces individually, which makes the whole thing a lot easier. That’s how this works.
Rather than throwing a wild guess out there at how fast the business might grow, you examine the history of its revenue growth, changes in profit margin, and changes in share count, to build a model for how it is likely to grow in the future.  You also should examine investor presentations and annual reports by the company, to see what management expects going forward in terms of growth in those various areas.
Keep in mind that these are forward-looking estimates. Don’t get too caught up in details or get too specific, since you can’t precisely predict the future anyway. It’s a back-of-the-envelope calculation for fair value based on conservative estimates of what is likely to occur.
**Ask yourself:**

How has sales volume changed in the past?  How will it probably change in the future? Is this a cyclical industry with ups and downs or a defensive and smooth-growing one?
Is there any reason to expect pricing to differ from inflation going forward? Has company management offered an estimate of top line (revenue) growth going forward?
How has the margin changed? Is there any reason to expect it to change going forward? Does the company have fixed costs, or do their costs change with volume?  Does management have a specific plan for margin improvement?
Is the company buying back shares, or issuing shares? Will this trend likely continue? What did company management say about this?
Is the dividend payout ratio low or high? Has it been growing faster than EPS? Does it have room to safely grow more?

Once you have all those inputs, you can use that to determine the fair price to pay for a stock. Here’s the output for this example:

Source: StockDelver
This stock is worth about $69.32, assuming the growth estimates are accurate.
If you can buy shares of the stock for lower than that amount, it should result in a good rate of return over the long term.
## Limitations of the Discounted Cash Flow Method

Once you have a system for evaluating whole businesses or individual stocks or projects or whatever your application may be, the math is easy. The hard part is predicting the future.
Estimating all the future cash flows that an investment should produce, discounting them to their present value, and summing them all together into the fair value of the investment, is both an art and a science.
If your investment achieves the future cash flows that you expect, then this equation will mathematically solve the variable you are looking for, whether it’s the fair price or the expected rate of return. If you know the future cash flows and your target rate of return, this will scientifically tell you the maximum you should pay for the investment.
The problem is that your estimate of future cash flows needs to be accurate, which is why this is also an art. If you are wrong about the future cash flows that you’ll receive, then the equation won’t be useful for you. Sometimes projects fail, and sometimes businesses encounter obstacles that nobody expected, and these things can disrupt cash flow. Alternatively, a product might sell 10x more than anyone thought, and the future cash flows could be far higher than anyone dared to hope.
Since none of us can see the future, the future cash flows that we place into the equation are only estimates. The best we can do is break the problem into small pieces, and ensure that our estimates for those pieces are reasonable.
To compensate for this, experienced investors do two things.
First, they apply a margin of safety. If they calculate that a stock is worth $50, they only buy it if it's under $45. If they calculate a business is worth $1 million, they'll walk away from the offer unless they can get it for $900,000. That way, even if the company doesn't perform quite as well as they expected, they have a margin for error to still get the rate of return they're hoping for.
Second, they diversify into numerous investments. No matter how much work you do, an investment could turn out badly. By splitting their wealth up into multiple projects, businesses, stocks, or properties, they reduce their risk as a whole.
When these two methods are combined, it means that you systematically evaluate the fair value of investments, only buy them at prices that are well below their fair value, and diversify enough so that even when you're wrong occasionally, you still come out ahead.
## Final Words

Discounted cash flow analysis is a powerful framework for determining the fair value of any investment that is expected to produce cash flow. Just about any other valuation method is an offshoot of this method in one way or another.
It works for private businesses, publicly traded stocks, projects, real estate, and any other investment that is expected to produce cash flow later in exchange for cash flow today.
If you want to apply it to stocks, check out StockDelver, which is my digital book and streamlined set of Excel calculators for valuing stocks.
In addition, if you want to get information on undervalued sectors or attractively-priced stocks, join my free investment newsletter and get a detailed update on market conditions and investment opportunities. It publishes approximately every 6 weeks.
**Further Reading:**

How to Determine if a Market is Overvalued
How to Value Gold and Silver
Contrarian/Value Investing: Why it Outperforms*Tweet[**Share](https://www.linkedin.com/cws/share?url=https%3A%2F%2Fwww.lynalden.com%2Fdiscounted-cash-flow-analysis%2F)[**Share](https://www.facebook.com/share.php?u=https%3A%2F%2Fwww.lynalden.com%2Fdiscounted-cash-flow-analysis%2F)